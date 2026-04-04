import { mdToPdf } from 'md-to-pdf';
import fs from 'fs';

export async function generatePdf(markdownText: string, outputPath: string): Promise<boolean> {
    try {
        if (process.env.VERCEL) {
            console.warn("Skipping Puppeteer PDF generation on Vercel due to missing Chrome binaries.");
            // You can write a dummy PDF or just return false
            return false;
        }
        await mdToPdf({ content: markdownText }, { dest: outputPath });
        return true;
    } catch (error) {
        console.error("Failed to generate PDF:", error);
        return false;
    }
}
