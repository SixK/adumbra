<template>
  <div>
    <i
      class="fa fa-plus"
      style="float: right; margin: 0 4px; color: green"
      @click="createMetadata"
    />

    <p
      class="title"
      style="margin: 0"
    >
      {{ title }}
    </p>

    <div class="row">
      <div class="col-sm">
        <p class="subtitle">
          {{ keyTitle }}
        </p>
      </div>
      <div class="col-sm">
        <p class="subtitle">
          {{ valueTitle }}
        </p>
      </div>
    </div>

    <ul
      class="list-group"
      style="height: 50%"
    >
      <li
        v-if="metadataList.length == 0"
        class="list-group-item meta-item"
      >
        <i class="subtitle">No items in metadata.</i>
      </li>
      <li
        v-for="(object, index) in metadataList"
        :key="index"
        class="list-group-item meta-item"
      >
        <div
          class="row"
          style="cell"
        >
          <div class="col-sm">
            <input
              v-model="object.key"
              type="text"
              class="meta-input"
              :placeholder="keyTitle"
            >
          </div>

          <div class="col-sm">
            <input
              v-model="object.value"
              type="text"
              class="meta-input"
              :placeholder="valueTitle"
            >
          </div>
        </div>
      </li>
    </ul>
  </div>
</template>

<script setup>

import { ref, watchEffect, onMounted } from 'vue';

const metadata = defineModel('metadata', { type: Object, required: true });
const title = defineModel('title', { type: String, default: "Metadata" });
const keyTitle = defineModel('keyTitle', { type: String, default: "Keys" });
const valueTitle = defineModel('valueTitle', { type: String, default: "Values" });
const exclude = defineModel('exclude', { type: String, default: "" });


const metadataList = ref([]);

const exportMetadata = () => {
  let new_metadata = {};
  metadataList.value.forEach((object) => {

    if (object.key.length > 0) {
      if (!isNaN(object.value))
        new_metadata[object.key] = parseInt(object.value);
      else if (
        object.value.toLowerCase() === "true" ||
        object.value.toLowerCase() === "false"
      )
        new_metadata[object.key] = object.value.toLowerCase() === "true";
      else new_metadata[object.key] = object.value;
    }
  });

  return new_metadata;
};



watchEffect(() => {
    loadMetadata();
});


onMounted(() => {
    // loadMetadata();
});



const createMetadata = () => {
  metadataList.value.push({ key: "", value: "" });
};

function loadMetadata() {
    if (metadata.value != null && metadata.value['metadata'] == null) {
      for (let key in metadata.value) {
        if (!Object.prototype.hasOwnProperty.call(metadata.value, key)) {
          continue;
        }
        if (typeof metadata.value[key] === 'function' 
               || typeof metadata.value[key] === 'object') {
            continue;
        }
        
        if (key === exclude.value) continue;
        let value = metadata.value[key];
        if (value == null) value = '';
        else value = value.toString();
        metadataList.value.push({ key: key, value: value });
      }
    }
};

defineExpose({exportMetadata, metadataList});

</script>

<style scoped>
.meta-input {
  padding: 3px;
  background-color: inherit;
  width: 100%;
  height: 100%;
  border: none;
}

.meta-item {
  padding: 3px;
  background-color: inherit;
  height: 40px;
  border: none;
}

.subtitle {
  margin: 0;
  font-size: 10px;
}
</style>
