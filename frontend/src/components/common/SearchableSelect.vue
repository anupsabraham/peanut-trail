<script setup lang="ts">

import {computed, onBeforeUnmount, onMounted, ref, watch} from "vue";

const props = defineProps<{
  modelValue: string
  options: string[]
  placeholder?: string
  allowEmpty?: boolean
  inputClass?: string
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: string): void
}>()

const search = ref(props.modelValue)
const open = ref(false)

const root = ref<HTMLElement>()

watch(
    () => props.modelValue,
    value => {
      search.value = value
    }
)

const filteredOptions = computed(() => {
  if (!search.value)
    return props.options
  return props.options.filter(option =>
      option.toLowerCase().includes(search.value.toLowerCase())
  )
})

function select(value: string) {
  search.value = value
  emit('update:modelValue', value)
  open.value = false
}

function onFocus() {
  open.value = true
  search.value = ""
}

function clearSelection() {
  search.value = ""
  emit("update:modelValue", "")
  open.value = false
}

function handleClick(event: MouseEvent) {
  if (!root.value?.contains(event.target as Node)) {
    open.value = false
    search.value = props.modelValue
  }
}

onMounted(() => {
  document.addEventListener('click', handleClick)
})

onBeforeUnmount(() => {
  document.removeEventListener('click', handleClick)
})

</script>

<template>
  <div ref="root" class="relative">
    <!-- Input -->
    <input
        v-model="search"
        @focus="onFocus"
        :placeholder="placeholder"
        :class="['w-full rounded border border-gray-200 focus:border-orange-400 focus:outline-none', inputClass || 'px-2 py-1 text-xs']"/>

    <!-- Dropdown -->
    <div
        v-if="open"
        class="absolute left-0 top-full z-50 mt-1 max-h-64 min-w-full overflow-y-auto rounded-md border border-gray-200 bg-white shadow-lg">
      <!-- All Categories -->
      <div
          v-if="allowEmpty"
          @click="clearSelection"
          :class="[
        'cursor-pointer border-b border-gray-100 px-3 py-2 text-sm',
        modelValue === ''
            ? 'bg-orange-100 font-medium text-orange-700'
            : 'hover:bg-orange-50',
    ]"
      >
        {{ placeholder || "All" }}
      </div>

      <!-- Existing options -->
      <div
          v-for="option in filteredOptions"
          :key="option"
          @click="select(option)"
          :class="['cursor-pointer px-3 py-2 text-sm whitespace-nowrap hover:bg-orange-50', option===modelValue && 'bg-orange-100 font-medium text-orange-700']"
          :title="option">
        {{ option }}
      </div>

      <!-- Create new -->
      <div
          v-if="filteredOptions.length === 0 && search.trim()"
          @click="select(search.trim())"
          class="cursor-pointer border-t border-gray-100 px-3 py-2 text-sm text-orange-600 hover:bg-orange-50">
        + Create "<strong>{{ search.trim() }}</strong>"
      </div>
    </div>
  </div>
</template>

<style scoped>

</style>