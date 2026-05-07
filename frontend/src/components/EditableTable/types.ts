/** EditableTable 行数据：稳定 `key` + 任意列字段 */
export type EditableTableRow = Record<string, unknown> & { key: string }

export type EditableTableColumn = {
  title: string
  dataIndex: string
  key: string
  width?: number
  ellipsis?: boolean
}
