/**
 * Utility to extract text from PDF files
 */
import * as pdfjsLib from 'pdfjs-dist';

// Set worker source - use reliable CDN
if (typeof window !== 'undefined') {
  // Use unpkg CDN (more reliable than cdnjs)
  // unpkg serves the exact version from npm registry
  pdfjsLib.GlobalWorkerOptions.workerSrc = `https://unpkg.com/pdfjs-dist@${pdfjsLib.version}/build/pdf.worker.min.js`;
  
  // Alternative fallback CDN (jsDelivr)
  // pdfjsLib.GlobalWorkerOptions.workerSrc = `https://cdn.jsdelivr.net/npm/pdfjs-dist@${pdfjsLib.version}/build/pdf.worker.min.js`;
}

export async function extractTextFromPDF(file: File): Promise<string> {
  try {
    // Ensure worker is loaded
    if (!pdfjsLib.GlobalWorkerOptions.workerSrc) {
      pdfjsLib.GlobalWorkerOptions.workerSrc = `https://unpkg.com/pdfjs-dist@${pdfjsLib.version}/build/pdf.worker.min.js`;
    }
    
    const arrayBuffer = await file.arrayBuffer();
    
    // Load PDF document with better error handling
    const loadingTask = pdfjsLib.getDocument({
      data: arrayBuffer,
      useSystemFonts: true,
      verbosity: 0, // Suppress console warnings
    });
    
    const pdf = await loadingTask.promise;
    
    let fullText = '';
    const maxPages = Math.min(pdf.numPages, 50); // Limit to 50 pages for performance
    
    // Extract text from all pages
    for (let pageNum = 1; pageNum <= maxPages; pageNum++) {
      try {
        const page = await pdf.getPage(pageNum);
        const textContent = await page.getTextContent();
        const pageText = textContent.items
          .map((item: any) => {
            // Handle text items
            if (item.str) {
              return item.str;
            }
            return '';
          })
          .filter((text: string) => text.trim().length > 0)
          .join(' ');
        
        if (pageText.trim()) {
          fullText += pageText + '\n\n';
        }
      } catch (pageError) {
        console.warn(`Error extracting text from page ${pageNum}:`, pageError);
        // Continue with other pages
      }
    }
    
    if (pdf.numPages > maxPages) {
      console.warn(`PDF has ${pdf.numPages} pages, only processed first ${maxPages} pages`);
    }
    
    if (!fullText.trim()) {
      throw new Error('PDF appears to be empty or contains no extractable text');
    }
    
    return fullText.trim();
  } catch (error) {
    console.error('Error extracting text from PDF:', error);
    const errorMessage = error instanceof Error ? error.message : 'Unknown error';
    
    // Provide more helpful error messages
    if (errorMessage.includes('worker') || errorMessage.includes('Failed to fetch')) {
      throw new Error(`PDF worker failed to load. Please check your internet connection and try again. If the problem persists, try refreshing the page.`);
    } else if (errorMessage.includes('Invalid PDF') || errorMessage.includes('invalid')) {
      throw new Error(`Invalid PDF file. Please ensure the file is a valid PDF document.`);
    } else {
      throw new Error(`Failed to extract text from PDF: ${errorMessage}. Please ensure the file is a valid PDF.`);
    }
  }
}

