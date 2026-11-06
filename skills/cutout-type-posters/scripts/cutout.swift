// Subject cutout with Apple Vision, fully on-device.
//
// Requires macOS 14 (Sonoma) or later: VNGenerateForegroundInstanceMaskRequest is new in macOS 14.
// Usage:  swift cutout.swift <in.png> <out-cutout.png> <out-mask.png>
//   out-cutout.png  the photo with everything except the subject(s) transparent, same size as the input
//   out-mask.png    the soft subject mask (white = subject), same size as the input
// Exits 1 with "no subject found" when Vision cannot find a foreground subject.
// Normally called by prep.sh, which also builds the graded and composite assets from the mask.
import Foundation
import Vision
import CoreImage
import CoreImage.CIFilterBuiltins
import ImageIO
import UniformTypeIdentifiers

let args = CommandLine.arguments
guard args.count == 4 else { print("usage: cutout in out-cutout out-mask"); exit(2) }
let inURL = URL(fileURLWithPath: args[1])
guard let src = CGImageSourceCreateWithURL(inURL as CFURL, nil),
      let cg = CGImageSourceCreateImageAtIndex(src, 0, nil) else { print("cannot read input"); exit(1) }

let req = VNGenerateForegroundInstanceMaskRequest()
let handler = VNImageRequestHandler(cgImage: cg, options: [:])
do { try handler.perform([req]) } catch { print("vision failed: \(error)"); exit(1) }
guard let obs = req.results?.first else { print("no subject found"); exit(1) }
print("instances: \(obs.allInstances.count)")

let ctx = CIContext()
func write(_ img: CIImage, _ path: String) {
  let url = URL(fileURLWithPath: path)
  guard let out = ctx.createCGImage(img, from: img.extent),
        let dest = CGImageDestinationCreateWithURL(url as CFURL, UTType.png.identifier as CFString, 1, nil) else {
    print("cannot write \(path)"); exit(1)
  }
  CGImageDestinationAddImage(dest, out, nil)
  CGImageDestinationFinalize(dest)
}

do {
  let cut = try obs.generateMaskedImage(ofInstances: obs.allInstances, from: handler, croppedToInstancesExtent: false)
  write(CIImage(cvPixelBuffer: cut), args[2])
  let mask = try obs.generateScaledMaskForImage(forInstances: obs.allInstances, from: handler)
  write(CIImage(cvPixelBuffer: mask), args[3])
  print("ok")
} catch { print("mask failed: \(error)"); exit(1) }
