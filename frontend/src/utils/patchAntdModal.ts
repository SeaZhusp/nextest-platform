/**
 * 全局：Modal 静态方法（confirm / info / success 等）点击遮罩不关闭。
 * 模板里 `<a-modal />` 请使用 `:mask-closable="false"`（或本文件末尾对组件的补丁）。
 */
import { Modal } from 'ant-design-vue'

function withNoMaskClose(fn: (props: Record<string, unknown>) => unknown) {
  return (props: Record<string, unknown>) =>
    fn({
      ...props,
      maskClosable: false
    })
}

const M = Modal as Record<string, unknown>

M.confirm = withNoMaskClose(Modal.confirm as (props: Record<string, unknown>) => unknown)
M.info = withNoMaskClose(Modal.info as (props: Record<string, unknown>) => unknown)
M.success = withNoMaskClose(Modal.success as (props: Record<string, unknown>) => unknown)
M.error = withNoMaskClose(Modal.error as (props: Record<string, unknown>) => unknown)
M.warning = withNoMaskClose(Modal.warning as (props: Record<string, unknown>) => unknown)
if (typeof (Modal as { warn?: typeof Modal.confirm }).warn === 'function') {
  M.warn = withNoMaskClose(
    (Modal as { warn: (props: Record<string, unknown>) => unknown }).warn
  )
}
