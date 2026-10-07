 An AI second-opinion system for doctors (not a replacement) that reads medical images + patient notes, localizes abnormalities, and gives evidence-backed findings with confidence.


Build an AI that doctors can use as second opinion. It reads X-ray/CT, combines with patient notes/test results, points to EXACT region where it sees something unusual, explains what it found, and tells confidence.

Key Idea: A finding with NO location in image OR NO supporting clinical notes = Hallucination = FAIL that case.

  Key Rules 
1.  Every finding must be backed up: Either point to a region in the image  + heatmap OR cite info from patient notes. Unsupported findings = hallucination = fail.
2.  Must include confidence levels: "I'm 95% sure" vs "I'm 30% sure" - don't say everything with certainty.
3.  Must present as helper, not doctor: Say "Doctor, consider this finding..." NOT "The patient has..."

  Our Solution :
            MedVision AI
1.  Detect: Abnormality in Chest X-ray (Pneumonia opacity, Nodule, Fracture, Pleural Effusion)
2.  Localize: YOLOv8 + Grad-CAM Heatmap to draw box on exact region - PROOF
3.  Understand Notes: BioClinicalBERT reads patient notes (fever, cough, WBC, age)
4.  Fuse: Combines Image + Notes together (Multimodal Fusion)
5.  Report: Gives finding + location + evidence + confidence + doctor-friendly note

 
