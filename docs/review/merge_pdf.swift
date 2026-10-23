// Merge PDFs into one, with a top-level bookmark per input.
// Usage: swift merge_pdf.swift OUT.pdf TITLE1 IN1.pdf [TITLE2 IN2.pdf ...]
import PDFKit

let args = Array(CommandLine.arguments.dropFirst())
let out = PDFDocument()
let outline = PDFOutline()
for i in stride(from: 1, to: args.count, by: 2) {
    guard let doc = PDFDocument(url: URL(fileURLWithPath: args[i + 1])) else {
        fatalError("cannot open \(args[i + 1])")
    }
    let start = out.pageCount
    for p in 0..<doc.pageCount { out.insert(doc.page(at: p)!, at: out.pageCount) }
    let item = PDFOutline()
    item.label = args[i]
    item.destination = PDFDestination(page: out.page(at: start)!, at: NSPoint(x: 0, y: 10000))
    outline.insertChild(item, at: outline.numberOfChildren)
}
out.outlineRoot = outline
guard out.write(to: URL(fileURLWithPath: args[0])) else { fatalError("cannot write \(args[0])") }
print("\(args[0]): \(out.pageCount) pages")
