# C7 Figure 7-4 Joint Letter Checkpoint

## Final commits

- 583a1be  aligned Joint Letter sender-symbol block lines with shared x starts
- 48c7f73  hardened Figure 7-4 audit for sender-symbol block internal alignment
- 7e11ab7  added production Figure 7-4 From-to-To gap audit rule
- 0b2f8a3  fixed Joint Letter From-block spacing
- 8255d65  aligned Joint Letter signature columns
- c04fceb  corrected two-signature horizontal placement
- 1b71336  updated Figure 7-4 signature profile regions
- f5a5b3b  restored body-to-signature gap
- c733b6b  pruned Joint Letter debug artifacts
- 2d57e7d  normalized Joint Letter heading and sender-symbol font
- 56a272e  normalized Joint Letter From/To/Subj label font
- 64c0bd0  corrected Joint Letter From block order and spacing

## Final layout rules captured

- Each Joint Letter sender-symbol block must use one shared left x start for all lines in that block.
- Left sender-symbol block lines share x=72.0.
- Right sender-symbol block lines share x=487.7.
- Sender-symbol block lines must not be independently centered or right-aligned per line.
- Senior command appears first in the letterhead and From block.
- Senior signer appears on the right.
- Non-senior signer appears on the left.
- Left signature block starts at the left margin.
- Right signature block starts at the standard signature start / page center.
- Signature title/role lines align under each signer name.
- Paragraph 4 to signature row must have a visible hard-return gap.
- Copy to remains below the signature title/role lines.
- Sender-symbol/date block uses Times-Roman 12 pt.
- JOINT LETTER heading uses Times-Roman 12 pt and starts at the left margin.
- From/To/Subj labels use Times-Roman 12 pt to match Figure 7-4.
- Header/body/signature content uses Times-Roman 12 pt.
- The first From command appears on the same baseline as "From:".
- The second From command appears one line below and aligns under the first From command text.
- The Figure 7-4 From block uses figure order: Naval Sea Systems Command first, Naval Supply Systems Command second.
- There is one visible blank-line gap between the second From command and the To line.

## Final measured Figure 7-4 positions

- final paragraph 4 line y=438.0
- From label x=72.0, y=178.76
- first From command x=115.0, y=178.76
- second From command x=115.0, y=193.16
- To label x=72.0, y=221.96
- second From command to To label gap=28.8 pt
- J. K. JANICKI x=72.0, y=510.0
- A. N. PIDGEON x=306.0, y=510.0
- Acting x=72.0, y=524.4
- Deputy x=306.0, y=524.4
- Copy to y=567.6
- final paragraph 4 line to signature row gap=72.0 pt
- Acting/Deputy to Copy to gap=43.2 pt

## Audit Hardening Proof

- Positive control passed 36/36 checks.
- Negative right-block alignment test failed as expected.
- Failure check: right_sender_symbol_block_x_alignment.
- Normal right block x starts: NAVSUP=487.7, Ser 07/207=487.7, 16 Jan 15=487.7.
- Mutated right block x starts: NAVSUP=492.0, Ser 07/207=487.7, 16 Jan 15=494.0.
- This proves the production profile catches misaligned right sender-symbol block lines.

## Known Audit Limitations

- Right-side 5216 is not currently included in the right sender-symbol alignment group because duplicate text lookup grabs the left-side 5216 first.
- Future audit-tool improvement: support region-qualified or instance-qualified span lookup so duplicate text can be checked independently.

## Notes

- The production audit now catches:
  - From: alone on its own line.
  - Wrong command on the From: baseline.
  - Collapsed From-to-To gap.
  - Misaligned sender-symbol block lines.

## Validation

- Figure 7-4 audit PASS
- C7 PASS
- C8 PASS
- C9 PASS
- C10 PASS
