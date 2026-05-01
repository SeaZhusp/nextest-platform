<script setup lang="ts">
// @ts-expect-error bytemd runtime exports under verbatimModuleSyntax
import { Editor, Viewer } from '@bytemd/vue-next'
import 'bytemd/dist/index.css'
import 'highlight.js/styles/github.css'
import { computed } from 'vue'
import gfm from '@bytemd/plugin-gfm'
import highlight from '@bytemd/plugin-highlight'

const props = defineProps<{
  preview: boolean
}>()

const markdown = defineModel<string>('markdown', { required: true })

const emit = defineEmits<{
  edited: []
}>()

const plugins = [gfm(), highlight()]

const markdownText = computed({
  get: () => markdown.value,
  set: (value: string) => {
    markdown.value = value
    emit('edited')
  }
})

function handleEditorChange(v: string) {
  markdownText.value = v
}

async function uploadImages() {
  return []
}
</script>

<template>
  <div class="output-markdown">
    <Viewer v-if="props.preview" class="markdown-viewer" :value="markdownText" :plugins="plugins" />
    <Editor
      v-else
      class="markdown-editor"
      :value="markdownText"
      :plugins="plugins"
      mode="split"
      :upload-images="uploadImages"
      @change="handleEditorChange"
    />
  </div>
</template>

<style scoped lang="scss">
.output-markdown {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0;
  background: #fff;
}

.markdown-editor,
.markdown-viewer {
  height: 100%;
  min-height: 0;
}

.markdown-editor {
  :deep(.bytemd) {
    height: 100%;
    border: none;
    background: #fff;
  }

  :deep(.bytemd-toolbar) {
    border-bottom: 1px solid #f0f0f0;
    padding: 6px 8px;
    overflow-x: auto;
    overflow-y: hidden;
    white-space: nowrap;
    scrollbar-width: thin;
  }

  :deep(.bytemd-toolbar::-webkit-scrollbar) {
    height: 6px;
  }

  :deep(.bytemd-toolbar::-webkit-scrollbar-thumb) {
    background: #d9d9d9;
    border-radius: 999px;
  }

  :deep(.bytemd-toolbar-left),
  :deep(.bytemd-toolbar-right) {
    display: inline-flex;
    gap: 2px;
    align-items: center;
  }

  :deep(.CodeMirror) {
    min-height: 320px;
    font-size: 13px;
    line-height: 1.55;
  }

  :deep(.CodeMirror-gutters) {
    border-right: 1px solid #f0f0f0;
  }

  :deep(.bytemd-preview) {
    background: #fcfcfc;
    border-left: 1px solid #f0f0f0;
  }
}

.markdown-viewer {
  padding: 16px 20px;
  overflow: auto;
  background: #fff;

  :deep(.markdown-body) {
    max-width: 860px;
    color: #1f2328;
  }
}
</style>
