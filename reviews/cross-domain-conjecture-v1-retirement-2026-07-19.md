# Cross-domain conjecture v1 eval retirement

Status: retired before baseline and before first commit.

The v1 loop encoded a single full-conjecture output shape while two negative
holdouts required rejection. When the prompt was corrected to a discriminated
`conjecture | rejection` result, all ten active cases passed but both sealed v1
holdouts retained the incompatible pre-union checks. They were not edited to
manufacture a pass. The entire uncommitted loop was retired and replaced by a
newly audited v2 contract and newly sealed holdouts.

Receipts:

- Original sealed holdout digest (unchanged throughout v1 iteration):
  `sha256:bc7f6d5e6d681e3452c16d840e3e1ab72ce310370c8f2a906b13adf60df38a0c`
- First release run: `run-20260719T163100Z-0c86a0`, prompt version
  `pv-edd37d636c01957e`, aggregate `0.0833`, gate failed.
- Post-union release run: `run-20260719T164659Z-851ca5`, prompt version
  `pv-061dd7f11ac8b57c`, aggregate `0.8333`; all 10 active cases passed and
  both incompatible v1 holdouts failed.
- Runtime reports remain preserved under
  `/opt/workspace/runtime/prompteval/synaplex-6c3eb6/cross-domain-conjecture/runs/`.

No v1 baseline was accepted. No cached run was substituted.
