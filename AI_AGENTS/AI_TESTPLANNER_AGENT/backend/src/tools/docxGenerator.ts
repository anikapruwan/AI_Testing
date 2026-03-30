import * as fs from 'fs';
import { Document, Packer, Paragraph, TextRun, HeadingLevel } from 'docx';

export async function generateDocx(markdownText: string, outputPath: string): Promise<void> {
    const lines = markdownText.split('\n');
    const children: Paragraph[] = [];
    
    for (let line of lines) {
        let text = line.trim();
        if (!text) continue;
        
        let headingLevel = 0;
        let pText = text;
        const hashMatch = text.match(/^(#{1,6})\s(.*)/);
        if (hashMatch) {
            headingLevel = hashMatch[1].length;
            pText = hashMatch[2];
        }
        
        if (headingLevel > 0) {
            let hLevel: any = HeadingLevel.HEADING_1;
            if (headingLevel === 2) hLevel = HeadingLevel.HEADING_2;
            else if (headingLevel === 3) hLevel = HeadingLevel.HEADING_3;
            else if (headingLevel === 4) hLevel = HeadingLevel.HEADING_4;
            else if (headingLevel === 5) hLevel = HeadingLevel.HEADING_5;
            else if (headingLevel >= 6) hLevel = HeadingLevel.HEADING_6;
            
            children.push(new Paragraph({
                text: pText,
                heading: hLevel
            }));
        } else {
            children.push(new Paragraph({
                children: [new TextRun(pText)]
            }));
        }
    }
    
    const doc = new Document({
        sections: [{ properties: {}, children }]
    });
    
    const buffer = await Packer.toBuffer(doc);
    fs.writeFileSync(outputPath, buffer);
}
