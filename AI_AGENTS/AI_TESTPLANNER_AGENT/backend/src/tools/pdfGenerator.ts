import { mdToPdf } from 'md-to-pdf';

export async function generatePdf(markdownText: string, outputPath: string): Promise<void> {
    await mdToPdf({ content: markdownText }, { dest: outputPath });
}
