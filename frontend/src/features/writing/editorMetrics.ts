export interface EditorMetrics {
  wordCount: number
  paragraphCount: number
  selectedWordCount: number
}

export function countWords(content: string): number {
  return content.replace(/\s/g, '').length
}

export function countParagraphs(content: string): number {
  return content
    .split(/\n+/)
    .map((paragraph) => paragraph.trim())
    .filter(Boolean).length
}

export function getEditorMetrics(content: string, selection = ''): EditorMetrics {
  return {
    wordCount: countWords(content),
    paragraphCount: countParagraphs(content),
    selectedWordCount: countWords(selection),
  }
}
