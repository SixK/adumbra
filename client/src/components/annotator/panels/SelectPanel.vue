<template>
  <div v-show="showme">
    <PanelToggle
      v-model:show-text="select.hover.showText"
      name="Show Hover Text"
    />
  </div>
</template>

<script setup>
import { ref, inject, watchEffect } from 'vue';
import PanelToggle from "@/components/PanelToggle.vue";

const select = defineModel('select', { type: Object, required: true });

const showme = ref('false');
const getActiveTool = inject('getActiveTool');

watchEffect(() => {
    showme.value = select.value.name === getActiveTool();
});

</script>
