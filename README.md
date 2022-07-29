# Bitcoin Manim

A script that animates the execution of a given Bitcoin OPCODE

## Installation

`pip install manim ecdsa`

## Generate a video

`manim -pql main.py AnimOPCODESeq  `

## Note

### About signature key generation

Use ECDSA `Seckp256k1` for key generation

### About signatures and signature verification

Bitcoin rely on `der` encoding so make sure to generate signatures with `der` encoding.

## Limitations

This script only take in SCRIPT (OPCODE input Stack) and simulate any data that is normally fetched from Bitcoin.

### OP_CHECKSIG

To check the signature the constructed message is the whole given SCRIPT put inline, for instance:

```
sig
pubkey
OP_CHECKSIG
```

The message will be:

```
sha256(sig pubkey OP_CHECKSIG)
// will output 590de76ebef1dd0009e903494f57e2840992b8562bc76583efbd3608366ffed0
```