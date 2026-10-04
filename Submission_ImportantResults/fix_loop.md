# Fix-Loop Results and Summary

This document explains what changed between our previous version ("before") and updated version ("after"), how the changes were made, and whether our accuracy goals were met.

---

## 1. LiDAR Scanning Updates

We updated how we process room boundaries in LiDAR scans to improve measurement accuracy.

### Key Results
* **Kitchen Ceiling Height** (Laser actual measurement: $2.800\text{ m}$):
  * **Before:** Off by $4.65\text{ cm}$ ($2.7535\text{ m}$)
  * **After:** Off by $4.09\text{ cm}$ ($2.7591\text{ m}$)
  * **Improvement:** Reduced error by $0.56\text{ cm}$
  * **Result:** **Failed goal.** We predicted an error of $\le 2\text{ cm}$ and targeted a pass mark of $\le 1.5\text{ cm}$.

* **Side Effects in Other Rooms:**
  * **Hall height error:** Got slightly worse, increasing from $3.04\text{ cm}$ to $3.13\text{ cm}$.
  * **Corridor height error:** Regressed significantly, increasing from $1.46\text{ cm}$ to $6.72\text{ cm}$.

### What We Learned
Changing room boundary rules helped room length and width measurements, but it didn't solve the ceiling height bias and caused incorrect surface selections in other rooms.

---

## 2. Photo Reconstruction Updates

We updated photo processing using new depth estimates (Depth Pro) and camera alignment updates to scale room dimensions correctly.

### Correcting the Baseline Error
Our original report misidentified the worst room dimension error. 
* **Correction:** The true worst baseline measurement was the **corridor short side**, which was estimated at $4.44\text{ m}$ instead of the actual $0.81\text{ m}$—a **$448.15\%$ error**.

### Key Results After Fixes
* **Worst Room Dimension (Corridor Short Side):**
  * **Before:** $4.44\text{ m}$ ($448.15\%$ error)
  * **After:** $2.24\text{ m}$ ($176.54\%$ error)
  * **Improvement:** Reduced error by $271.60\text{ percentage points}$.
  * **Result:** **Failed goal.** Although significantly improved, it missed both our soft target ($<100\%$ error) and our required accuracy gate ($\pm 8\%$ error).

* **Other Measurements:**
  * **Corridor long side:** Improved from $5.56\text{ m}$ to $3.20\text{ m}$ ($91.62\%$ error vs. $1.67\text{ m}$ actual).
  * **Kitchen long side:** Improved from $7.60\text{ m}$ to $2.772\text{ m}$.

---

## 3. Standalone Kitchen Scan Improvements

When running a standalone scan of just the kitchen (excluding multi-room scans), performance improved noticeably.

* **Kitchen Ceiling Height:**
  * **Before:** Off by $1.62\text{ cm}$ ($2.7838\text{ m}$)
  * **After:** Off by $0.79\text{ cm}$ ($2.7921\text{ m}$)
  * **Result:** **Passed** the $\le 1.5\text{ cm}$ target.
* **Kitchen Floor Area Error:**
  * **Before:** Off by approx. $24.9\%$
  * **After:** Off by approx. $9.3\%$

*Takeaway:* This proves single-room fixes work under isolated conditions, but it does not mean overall multi-room height issues are completely solved.

