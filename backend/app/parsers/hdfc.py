"""Parsers for HDFC Bank statements."""

import csv
import io
import time
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import ClassVar

from app.parsers.resolver import StatementParser
from app.parsers.types import (
    FileType,
    ParsedTransaction,
    ParseIssue,
    ParseResult,
    StatementType,
    UnsupportedStatementError,
)


class HDFCSavingsCsvParser(StatementParser):
    """Parse HDFC savings-account CSV statements."""

    _COLUMN_ALIASES: ClassVar[dict[str, tuple[str, ...]]] = {
        "debit_date": ("Date",),
        "narration": ("Narration",),
        "txn_number": ("Chq/Ref Number", "Chq / Ref Number"),
        "actual_date": ("Value Dat", "Value Date"),
        "debit_amount": ("Debit Amount", "Withdrawal Amt."),
        "credit_amount": ("Credit Amount", "Deposit Amt."),
    }

    def parse(self, file_content: bytes) -> ParseResult:
        """Parse one statement without persisting any transaction.

        HDFC statements occasionally contain an unquoted comma in ``Narration``.
        Rows with extra fields are repaired only by joining those fields back into
        narration; all other malformed row layouts are reported to the caller.
        """
        try:
            content = file_content.decode("utf-8-sig")
        except UnicodeDecodeError:
            return ParseResult(
                issues=[
                    ParseIssue(
                        code="unsupported_encoding",
                        message="The statement must be encoded as UTF-8.",
                    )
                ]
            )

        result = ParseResult()
        try:
            reader = csv.reader(io.StringIO(content, newline=""), strict=True)
            header, header_row = self._find_statement_header(reader)
            if header is None:
                result.issues.append(
                    ParseIssue(
                        code="header_not_found",
                        message="Could not find the HDFC savings statement Date and Narration headers.",
                    )
                )
                return result

            columns, missing = self._resolve_savings_columns(header)
            if missing:
                result.issues.append(
                    ParseIssue(
                        code="required_columns_missing",
                        message=f"The statement is missing required columns: {', '.join(missing)}.",
                        source_row=header_row,
                        raw_values=tuple(header),
                    )
                )
                return result

            for row in reader:
                source_row = reader.line_num
                if not any(value.strip() for value in row):
                    continue
                self._parse_statement_row(result, row, source_row, header, columns)
        except csv.Error as error:
            result.issues.append(ParseIssue(code="invalid_csv", message=f"The CSV could not be read: {error}."))

        return result

    def _find_statement_header(self, reader: csv.reader) -> tuple[list[str] | None, int | None]:
        for row in reader:
            normalized = {self._normalize_header(value) for value in row}
            if self._normalize_header("Date") in normalized and self._normalize_header("Narration") in normalized:
                return [value.strip() for value in row], reader.line_num
        return None, None

    def _resolve_savings_columns(self, header: list[str]) -> tuple[dict[str, int], list[str]]:
        normalized_header = {self._normalize_header(value): index for index, value in enumerate(header)}
        columns: dict[str, int] = {}
        missing: list[str] = []
        for field, aliases in self._COLUMN_ALIASES.items():
            index = None
            for alias in aliases:
                index = normalized_header.get(self._normalize_header(alias))
                if index is not None:
                    break
            if index is None:
                missing.append(aliases[0])
            else:
                columns[field] = index
        return columns, missing

    def _parse_statement_row(
        self,
        result: ParseResult,
        row: list[str],
        source_row: int,
        header: list[str],
        columns: dict[str, int],
    ) -> None:
        raw_values = tuple(row)
        repaired_row, was_repaired = self._repair_unquoted_narration_commas(row, len(header), columns["narration"])
        if repaired_row is None:
            result.issues.append(
                ParseIssue(
                    code="column_count_mismatch",
                    message="The row does not match the statement columns and could not be safely repaired.",
                    source_row=source_row,
                    raw_values=raw_values,
                )
            )
            return

        values = {field: repaired_row[index].strip() for field, index in columns.items()}
        try:
            result.transactions.append(
                ParsedTransaction(
                    source_row=source_row,
                    debit_date=self._parse_statement_date(values["debit_date"]),
                    actual_date=self._parse_statement_date(values["actual_date"]),
                    narration=values["narration"],
                    txn_number=values["txn_number"],
                    debit_amount=self._parse_statement_amount(values["debit_amount"]),
                    credit_amount=self._parse_statement_amount(values["credit_amount"]),
                    raw_values=raw_values,
                    was_repaired=was_repaired,
                )
            )
        except (ValueError, InvalidOperation) as error:
            result.issues.append(
                ParseIssue(
                    code="invalid_transaction_data",
                    message=str(error),
                    source_row=source_row,
                    raw_values=raw_values,
                )
            )

    @staticmethod
    def _repair_unquoted_narration_commas(
        row: list[str], expected_columns: int, narration_index: int
    ) -> tuple[list[str] | None, bool]:
        if len(row) == expected_columns:
            return row, False
        if len(row) < expected_columns:
            return None, False

        extra_columns = len(row) - expected_columns
        narration_end = narration_index + extra_columns + 1
        repaired = [
            *row[:narration_index],
            ",".join(row[narration_index:narration_end]),
            *row[narration_end:],
        ]
        return repaired, True

    @staticmethod
    def _parse_statement_date(value: str) -> date:
        for date_format in ("%d/%m/%y", "%d/%m/%Y"):
            try:
                parsed = time.strptime(value, date_format)
                return date(parsed.tm_year, parsed.tm_mon, parsed.tm_mday)
            except ValueError:
                continue
        message = f"Invalid statement date: {value!r}"
        raise ValueError(message)

    @staticmethod
    def _parse_statement_amount(value: str) -> Decimal:
        cleaned = value.replace(",", "").strip()
        if not cleaned:
            return Decimal(0)
        try:
            return Decimal(cleaned)
        except InvalidOperation as error:
            message = f"Invalid statement amount: {value!r}"
            raise ValueError(message) from error

    @staticmethod
    def _normalize_header(value: str) -> str:
        return " ".join(value.strip().casefold().split())


def resolve_parser(statement_type: StatementType, file_type: FileType) -> StatementParser:
    """Return an HDFC parser for a supported statement/file combination."""
    if statement_type is StatementType.SAVINGS and file_type is FileType.CSV:
        return HDFCSavingsCsvParser()

    message = f"HDFC does not support {statement_type.value} statements in {file_type.value} format."
    raise UnsupportedStatementError(message)
