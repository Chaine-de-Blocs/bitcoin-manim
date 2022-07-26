import opcode
from manim import *
from enum import Enum
import hashlib
import ecdsa
from ecdsa.util import sigdecode_der

class OPCODE(Enum):
    OP_0 = 0
    OP_FALSE = 0
    OP_PUSHDATA1 = 76
    OP_PUSHDATA2 = 77
    OP_PUSHDATA4 = 78
    OP_1NEGATE = 79
    OP_1 = 81
    OP_TRUE = 81
    OP_2 = 82
    OP_3 = 83
    OP_4 = 84
    OP_5 = 85
    OP_6 = 86
    OP_7 = 87
    OP_8 = 88
    OP_9 = 89
    OP_10 = 90
    OP_11 = 91
    OP_12 = 92
    OP_13 = 93
    OP_14 = 94
    OP_15 = 95
    OP_16 = 96
    OP_VERIFY = 105
    OP_DUP = 118
    OP_EQUAL = 135
    OP_EQUALVERIFY = 136
    OP_ADD = 147
    OP_SUB = 148
    OP_MUL = 149
    OP_DIV = 150
    OP_MOD = 151
    OP_HASH160 = 169
    OP_HASH256 = 170
    OP_CHECKSIG = 172

class AnimOPCODESeq(Scene):
    def construct(self):
        # TODO check if stack valid
        self.in_stack = ["304502201fd8abb11443f8b1b9a04e0495e0543d05611473a790c8939f089d073f90509a022100f4677825136605d732e2126d09a2d38c20c75946cd9fc239c0497e84c634e3dd", "03301a8259a12e35694cc22ebc45fee635f4993064190f6ce96e7fb19a03bb6be2", OPCODE.OP_CHECKSIG]
        in_stack_mobj = []
        out_stack_mobj = []
        output_stack = []
        
        # Display the OPCODE input stack
        for idx, in_stack_value in enumerate(self.in_stack):
            name = f"&lt;{in_stack_value}&gt;"
            if type(in_stack_value) is not str:
                name = f"{in_stack_value.name}"
            opcode_text = MarkupText(name).scale(0.6).to_corner(UL)
            if len(in_stack_mobj) > 0:
                opcode_text.next_to(in_stack_mobj[idx - 1], DOWN).align_to(in_stack_mobj[idx - 1], LEFT)
            self.play(Write(opcode_text))
            in_stack_mobj.append(opcode_text)
            
        explain_mobj = MarkupText(f"Processing the SCRIPT").scale(0.4).to_corner(DOWN)
        self.play(FadeIn(explain_mobj))
        self.wait()

        for idx, in_stack_value in enumerate(self.in_stack):
            new_output_stack, explain, tx_invalid = self.process_opcode_output_stack(
                p_opcode=in_stack_value,
                p_output_stack=output_stack.copy(),
                current_index=idx
            )
            
            new_explain_mobj = MarkupText(explain).scale(0.4).to_corner(DOWN)
            self.play(
                Indicate(in_stack_mobj[idx]),
                Transform(explain_mobj, new_explain_mobj)
            )
            
            if tx_invalid:
                output_stack = new_output_stack
                break

            output_text = MarkupText(f"{str(new_output_stack[len(new_output_stack) - 1])}").scale(0.6)
            
            if idx == 0:
                output_text.next_to(in_stack_mobj[idx], RIGHT)
            else:
                output_text.next_to(out_stack_mobj[idx - 1], DOWN).align_to(out_stack_mobj[idx - 1], LEFT)

            self.play(Write(output_text))
            out_stack_mobj.append(output_text)
            
            if len(new_output_stack) <= len(output_stack):
                nb_unstack = len(output_stack) - len(new_output_stack) + 1
                if nb_unstack == 2:
                    self.play(
                        FadeOut(out_stack_mobj[len(out_stack_mobj) - 2], shift=RIGHT),
                        FadeOut(out_stack_mobj[len(out_stack_mobj) - 3], shift=RIGHT),
                        out_stack_mobj[len(out_stack_mobj) - 1].animate.move_to(out_stack_mobj[len(out_stack_mobj) - 3]).align_to(out_stack_mobj[len(out_stack_mobj) - 3], LEFT)
                    )
            
            output_stack = new_output_stack

            self.remove(explain_mobj)
            explain_mobj = new_explain_mobj
        
        last_output = output_stack.pop()
        if last_output == OPCODE.OP_VERIFY:
            end_text = MarkupText(f'This transaction fails because of <b><span fgcolor="{YELLOW}">OP_VERIFY</span></b>')
        elif last_output == OPCODE.OP_EQUALVERIFY:
            value_1, value_2 = self.read_output_stack_params(output_stack, 2)
            end_text = MarkupText(f'The values {value_1} and {value_2} are different. The transaction fails because it does not pass the {OPCODE.OP_VERIFY.name}')
        else:
            end_text = MarkupText(f'The Result is <b><span fgcolor="{YELLOW}">{last_output}</span></b>')
            
        self.play(Transform(explain_mobj, end_text))
        
    def process_opcode_output_stack(self, p_opcode, p_output_stack, current_index):
        explain = "Nothing happened"
        output = None
        tx_invalid = False
        if p_opcode == OPCODE.OP_0 or p_opcode == OPCODE.OP_1 or p_opcode == OPCODE.OP_2 or p_opcode == OPCODE.OP_3 or p_opcode == OPCODE.OP_4 or p_opcode == OPCODE.OP_5 or p_opcode == OPCODE.OP_5 or p_opcode == OPCODE.OP_6 or p_opcode == OPCODE.OP_7 or p_opcode == OPCODE.OP_8 or p_opcode == OPCODE.OP_9 or p_opcode == OPCODE.OP_10 or p_opcode == OPCODE.OP_11 or p_opcode == OPCODE.OP_12 or p_opcode == OPCODE.OP_13 or p_opcode == OPCODE.OP_14 or p_opcode == OPCODE.OP_15 or p_opcode == OPCODE.OP_16: # TODO all numbers to 16
            if p_opcode is not OPCODE.OP_0:
                output = p_opcode.value - 80
            else:
                output = 0
            explain = self.get_explain_for_push_value(p_opcode, output)
        elif p_opcode == OPCODE.OP_EQUAL:
            value_1, value_2 = self.read_output_stack_params(p_output_stack, 2)
            output = value_1 == value_2
            explain = f'{p_opcode.name} : Are the values <b><span fgcolor="{YELLOW}">{value_1}</span></b> and <b><span fgcolor="{YELLOW}">{value_2}</span></b> equals?'
        elif p_opcode == OPCODE.OP_ADD:
            value_1, value_2 = self.read_output_stack_params(p_output_stack, 2)
            output = value_1 + value_2
            explain = f'{p_opcode.name} : Adds the values <b><span fgcolor="{YELLOW}">{value_1}</span></b> and <b><span fgcolor="{YELLOW}">{value_2}</span></b>'
        elif p_opcode == OPCODE.OP_SUB:
            value_1, value_2 = self.read_output_stack_params(p_output_stack, 2)
            output = value_1 - value_2
            explain = f'{p_opcode.name} : Substacts the values <b><span fgcolor="{YELLOW}">{value_1}</span></b> and <b><span fgcolor="{YELLOW}">{value_2}</span></b>'
        elif p_opcode == OPCODE.OP_MUL:
            value_1, value_2 = self.read_output_stack_params(p_output_stack, 2)
            output = value_1 - value_2
            explain = f'{p_opcode.name} : Multiplies the values <b><span fgcolor="{YELLOW}">{value_1}</span></b> and <b><span fgcolor="{YELLOW}">{value_2}</span></b>'
        elif p_opcode == OPCODE.OP_DIV:
            value_1, value_2 = self.read_output_stack_params(p_output_stack, 2)
            output = value_1 - value_2
            explain = f'{p_opcode.name} : Divides the values <b><span fgcolor="{YELLOW}">{value_1}</span></b> and <b><span fgcolor="{YELLOW}">{value_2}</span></b>'
        elif p_opcode == OPCODE.OP_MOD:
            value_1, value_2 = self.read_output_stack_params(p_output_stack, 2)
            output = value_1 - value_2
            explain = f'{p_opcode.name} : Modulos the values <b><span fgcolor="{YELLOW}">{value_1}</span></b> and <b><span fgcolor="{YELLOW}">{value_2}</span></b>'
        elif p_opcode == OPCODE.OP_HASH256:
            value_1, _ = self.read_output_stack_params(p_output_stack, 1)
            h = hashlib.sha256()
            h.update(str.encode(value_1))
            output = h.hexdigest()
            explain = f'{p_opcode.name} : SHA256 Hashes the value <b><span fgcolor="{YELLOW}">{value_1}</span></b>'
        elif p_opcode == OPCODE.OP_HASH160:
            value_1, _ = self.read_output_stack_params(p_output_stack, 1)
            output = hashlib.new("ripemd160", str.encode(value_1)).hexdigest()
            explain = f'{p_opcode.name} : RIPEMD160 Hashes the value <b><span fgcolor="{YELLOW}">{value_1}</span></b>'
        elif p_opcode == OPCODE.OP_DUP:
            output = p_output_stack[len(p_output_stack) - 1]
            explain = f'{p_opcode.name} : Duplicates the value <b><span fgcolor="{YELLOW}">{output}</span></b>'
        elif p_opcode == OPCODE.OP_VERIFY:
            value_1, _ = self.read_output_stack_params(p_output_stack, 1)
            if value_1 != True:
                tx_invalid = True
                
            output = OPCODE.OP_VERIFY
                
            explain = f'{p_opcode.name} : Verifies if the last output value is <b><span fgcolor="{YELLOW}">True</span></b>'
        elif p_opcode == OPCODE.OP_EQUALVERIFY:
            value_1, value_2 = self.read_output_stack_params(p_output_stack, 2)
            tx_invalid = value_1 != value_2
            if tx_invalid:
                # Puts the values back to the stack
                # so we can display them in the fail message
                p_output_stack.append(value_2)
                p_output_stack.append(value_1)
                output = OPCODE.OP_EQUALVERIFY
            else:
                output = tx_invalid
            explain = f'{p_opcode.name} : Checks if <b><span fgcolor="{YELLOW}">{value_1}</span></b> and <b><span fgcolor="{YELLOW}">{value_2}</span></b> are equals. The transaction fails if they are not equals'
        elif p_opcode == OPCODE.OP_CHECKSIG:
            pubkey, sig = self.read_output_stack_params(p_output_stack, 2)
            
            # TODO construct a message
            message = bytes.fromhex("304502201fd8abb11443f8b1b9a04e0495e0543d05611473a790c8939f089d073f90509a022100f4677825136605d732e2126d09a2d38c20c75946cd9fc239c0497e84c634e3dd01")
            
            explain = f'{p_opcode.name} : Checks the signature for message <b><span fgcolor="{YELLOW}">{message}</span></b>'

            verif_key = ecdsa.VerifyingKey.from_string(bytes.fromhex(pubkey), curve=ecdsa.SECP256k1)
            try:
                verif_key.verify(bytes.fromhex(sig), message, hashlib.sha256, sigdecode=sigdecode_der)
            except ecdsa.BadSignatureError:
                output = False
        else:
            output = self.in_stack[current_index]
            explain = f'Reads the data <b><span fgcolor="{YELLOW}">{output}</span></b> from input stack'

        if output is not None:
            p_output_stack.append(output)

        return p_output_stack, explain, tx_invalid
    
    def get_explain_for_push_value(self, opcode, value):
        if value == 0:
            value = "0 or False"
        if value == 1:
            value = "1 or True"
        return f'{opcode.name} : Pushes the value <b><span fgcolor="{YELLOW}">{value}</span></b>'
    
    def read_output_stack_params(self, output_stack, nb_params):
        value_1 = output_stack.pop()
        value_2 = None
        if nb_params > 1:
            value_2 = output_stack.pop()

        return value_1, value_2