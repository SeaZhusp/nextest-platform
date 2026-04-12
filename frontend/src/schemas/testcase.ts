/** 与后端 app/schemas/testcase.py 对齐 */
export interface TestCaseItem {
  id?: string | null
  case_no: string
  module: string
  title: string
  preconditions?: string
  steps?: string
  expected?: string
  priority?: string
}
