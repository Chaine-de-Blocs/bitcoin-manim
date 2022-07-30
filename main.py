from ctypes import alignment
from manim import *
from enum import Enum
import hashlib
import ecdsa
from ecdsa.util import sigdecode_der, sigencode_der

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
    OP_IF = 99
    OP_ENDIF = 103
    OP_VERIFY = 105
    OP_RETURN = 106
    OP_DROP = 117
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
    OP_CLTV = 177
    
stack_bottom_margin = DOWN / 5
stack_top_elt = UP * 3

# TODO fetch this from a .yml
tx_data = {
    "n_lock_time": 4000,
    "n_sequence": 0xFFFFFFFF
}

class AnimOPCODESeq(Scene):
    def construct(self):
        # TODO check if stack valid
        
        # self.in_stack = [OPCODE.OP_1, OPCODE.OP_DROP]
        # self.generate_p2pkh_script()
        # self.generate_p2pk_script()
        # self.generate_puzzle()
        self.generate_freezing_funds()
        
        print("SCRIPT : ", self.in_stack)

        self.output_stack = []
        self.input_block_level = -1
        self.current_in_stack_mobj_idx = -1
        self.tx_invalid = False
        self.tx_invalid_reason = None
        
        self.in_stack_mobj = []
        self.out_stack_mobj = []
        self.output_stack_mobj_grp = Group()
        
        self.explain_mobj = MarkupText(f"Processing the SCRIPT", should_center=True).scale(0.4).to_corner(DOWN)
        self.play(FadeIn(self.explain_mobj))
            
        self.render_input_stack(self.in_stack)
        
        # decorates the input stack
        input_mobj_grp = Group()
        for _, obj in enumerate(self.in_stack_mobj):
            input_mobj_grp.add(obj)
        input_stack_framebox = SurroundingRectangle(input_mobj_grp, buff=.5, color=BLUE, corner_radius=.15)
        self.play(Create(input_stack_framebox))
        
        input_stack_title = Text("Input Stack (SCRIPT)", color=BLUE).scale(.6).next_to(input_stack_framebox, UP).align_to(input_stack_framebox, LEFT)
        self.play(Write(input_stack_title))
        
        self.render_output_stack(self.in_stack)
        
        transitive_text = Text("Finishing the SCRIPT").scale(0.4).to_corner(DOWN)
        self.play(
            Transform(self.explain_mobj, transitive_text)
        )
        
        output_stack_framebox = SurroundingRectangle(self.output_stack_mobj_grp, buff=.5, corner_radius=.15)
        self.play(Create(output_stack_framebox))

        output_stack_title = Text("Output Stack (RESULT)", color=YELLOW).scale(.6).next_to(output_stack_framebox, UP).align_to(output_stack_framebox, LEFT)
        self.play(Write(output_stack_title))        
        
        last_output = None if len(self.output_stack) == 0 else self.output_stack[-1]
        
        end_text_group = VGroup()
        if self.tx_invalid:
            print(f"This tx in invalid, failed at {last_output.name}, reason : {self.tx_invalid_reason}")
            end_text = MarkupText(f'This transaction fails because of <b><span fgcolor="{YELLOW}">{last_output.name}</span></b> ')
            end_text_group.add(end_text)
            if self.tx_invalid_reason is not None:
                end_text_group.add(MarkupText(self.tx_invalid_reason).scale(0.8).next_to(end_text, DOWN))
        else:
            print(f"This tx ended with {last_output}")
            if last_output == True:
                end_text_group.add(MarkupText(f'The Result is <b><span fgcolor="{YELLOW}">{last_output}</span></b>. This transaction is valid!'))
            else:
                end_text_group.add(MarkupText(f'The Result is <b><span fgcolor="{YELLOW}">{last_output}</span></b>. This transaction fails!'))
            
        print("Final output stack : ", self.output_stack)
        
        end_text_group.scale(0.8).to_corner(DOWN)

        self.play(
            Transform(self.explain_mobj, end_text_group)
        )
        
    def render_input_stack(self, input_block):
        self.input_block_level += 1

        for idx, in_stack_value in enumerate(input_block):
            if type(in_stack_value) == list:
                self.render_input_stack(in_stack_value)
                continue
            name = f"&lt;{self.format_value_for_render(in_stack_value)}&gt;"
            if type(in_stack_value) is OPCODE:
                name = f"{in_stack_value.name}"
                
            if len(name) > 18:
                name = name[:17] + "..."
                
            opcode_text = MarkupText(name).scale(0.5)
            if len(self.in_stack_mobj) == 0:
                opcode_text.to_corner(stack_top_elt).shift(LEFT * 3)
            else:
                opcode_text.next_to(self.in_stack_mobj[-1], stack_bottom_margin).align_to(self.in_stack_mobj[-1], LEFT)
                if in_stack_value == OPCODE.OP_ENDIF:
                    opcode_text.shift(LEFT / 3)
                if idx == 0 and self.input_block_level > 0:
                    opcode_text.shift(RIGHT / 3)
                    
            self.play(Write(opcode_text))
            self.in_stack_mobj.append(opcode_text)
            
        self.input_block_level -= 1
    
    def render_output_stack(self, input_block):
        for idx, in_stack_value in enumerate(input_block):
            if self.tx_invalid:
                break

            # a list a new block, it's been processed by recursion when processing OPCODE
            # see enter_next_input_block
            if type(in_stack_value) == list:
                continue
        
            self.current_in_stack_mobj_idx += 1

            read_output_values, write_output_values, explain, enter_next_input_block = self.process_opcode_output_stack(
                p_opcode=in_stack_value,
                input_block=input_block,
                current_in_idx=idx
            )
            
            new_explain_mobj = MarkupText(explain, should_center=True).scale(0.4).to_corner(DOWN)
            self.play(
                Indicate(self.in_stack_mobj[self.current_in_stack_mobj_idx]),
                Transform(self.explain_mobj, new_explain_mobj)
            )
            
            self.update_output_mobj(read_output_values, write_output_values, in_stack_value)
        
            if enter_next_input_block:
                self.render_output_stack(input_block[idx + 1])
                continue

            self.remove(self.explain_mobj)
            self.explain_mobj = new_explain_mobj
            
        return read_output_values
    
    def update_output_mobj(self, read_values, write_values, opcode):            
        if self.tx_invalid:
            return

        output_text = None
        if len(write_values) > 0:
            output_text = MarkupText(f"{self.format_value_for_render(str(write_values[-1]))}").scale(0.5)
        
        if output_text is not None:
            if len(self.out_stack_mobj) == 0:
                output_text.to_corner(stack_top_elt).shift(RIGHT * 3)
            else:
                output_text.next_to(self.out_stack_mobj[-1], stack_bottom_margin).align_to(self.out_stack_mobj[-1], LEFT)

            self.output_stack_mobj_grp.add(output_text)
            self.play(Write(output_text))
            self.out_stack_mobj.append(output_text)

        if len(read_values) > 0:
            stack_grp = Group()
            remove_mobj_idx = []
            last_mobj = None
            for i in range(len(read_values)):
                mobj_idx = len(self.out_stack_mobj) - (1 + i + len(write_values))
                remove_mobj_idx.append(mobj_idx)
                last_mobj = self.out_stack_mobj[mobj_idx]
                stack_grp.add(last_mobj)
                
            read_values_grp = VGroup()
            # updates the mobj list to be coherent with the output stack
            for _, mobj_idx in enumerate(remove_mobj_idx):
                read_values_grp.add(self.out_stack_mobj.pop(mobj_idx))

            # line to give rotate direction
            dir_line = Line()                
            read_values_brace = Brace(read_values_grp, sharpness=.1, direction=dir_line.rotate(PI * 2).get_unit_vector())
            self.play(FadeIn(read_values_brace, shift=RIGHT / 4))
            
            read_values_text = Text(f"{opcode.name} params").scale(0.3).next_to(read_values_brace, RIGHT)
            self.play(Write(read_values_text))
            
            # updates the stack it read values and write some
            if len(write_values) > 0:
                self.play(
                    FadeOut(stack_grp, shift=RIGHT),
                    FadeOut(read_values_brace, shift=RIGHT),
                    FadeOut(read_values_text, shift=RIGHT),
                    self.out_stack_mobj[-1].animate.move_to(last_mobj).align_to(last_mobj, LEFT)
                )
            # only removes the read stack
            else:
                self.play(
                    FadeOut((stack_grp), shift=RIGHT),
                    FadeOut(read_values_brace, shift=RIGHT),
                    FadeOut(read_values_text, shift=RIGHT)
                )

    def process_opcode_output_stack(self, p_opcode, input_block, current_in_idx):
        explain = None
        output = None
        enter_next_input_block = False
        read_output_values = []
        write_output_values = []
        if p_opcode == OPCODE.OP_0 or p_opcode == OPCODE.OP_1 or p_opcode == OPCODE.OP_2 or p_opcode == OPCODE.OP_3 or p_opcode == OPCODE.OP_4 or p_opcode == OPCODE.OP_5 or p_opcode == OPCODE.OP_5 or p_opcode == OPCODE.OP_6 or p_opcode == OPCODE.OP_7 or p_opcode == OPCODE.OP_8 or p_opcode == OPCODE.OP_9 or p_opcode == OPCODE.OP_10 or p_opcode == OPCODE.OP_11 or p_opcode == OPCODE.OP_12 or p_opcode == OPCODE.OP_13 or p_opcode == OPCODE.OP_14 or p_opcode == OPCODE.OP_15 or p_opcode == OPCODE.OP_16: # TODO all numbers to 16
            if p_opcode is not OPCODE.OP_0:
                output = p_opcode.value - 80
            else:
                output = 0
            explain = self.get_explain_for_push_value(p_opcode, output)
        elif p_opcode == OPCODE.OP_EQUAL:
            read_output_values = self.read_output_stack_params(2)
            output = read_output_values[0] == read_output_values[1]
            explain = f'{p_opcode.name} : Are the values <b><span fgcolor="{YELLOW}">{self.format_value_for_render(read_output_values[0])}</span></b> and <b><span fgcolor="{YELLOW}">{self.format_value_for_render(read_output_values[1])}</span></b> equals?'
        elif p_opcode == OPCODE.OP_ADD:
            read_output_values = self.read_output_stack_params(2)
            output = read_output_values[0] + read_output_values[1]
            explain = f'{p_opcode.name} : Adds the values <b><span fgcolor="{YELLOW}">{read_output_values[0]}</span></b> and <b><span fgcolor="{YELLOW}">{read_output_values[1]}</span></b>'
        elif p_opcode == OPCODE.OP_SUB:
            read_output_values = self.read_output_stack_params(2)
            output = read_output_values[0] - read_output_values[1]
            explain = f'{p_opcode.name} : Substacts the values <b><span fgcolor="{YELLOW}">{read_output_values[0]}</span></b> and <b><span fgcolor="{YELLOW}">{read_output_values[1]}</span></b>'
        elif p_opcode == OPCODE.OP_MUL:
            read_output_values = self.read_output_stack_params(2)
            output = read_output_values[0] - read_output_values[1]
            explain = f'{p_opcode.name} : Multiplies the values <b><span fgcolor="{YELLOW}">{read_output_values[0]}</span></b> and <b><span fgcolor="{YELLOW}">{read_output_values[1]}</span></b>'
        elif p_opcode == OPCODE.OP_DIV:
            read_output_values = self.read_output_stack_params(2)
            output = read_output_values[0] - read_output_values[1]
            explain = f'{p_opcode.name} : Divides the values <b><span fgcolor="{YELLOW}">{read_output_values[0]}</span></b> and <b><span fgcolor="{YELLOW}">{read_output_values[1]}</span></b>'
        elif p_opcode == OPCODE.OP_MOD:
            read_output_values = self.read_output_stack_params(2)
            output = read_output_values[0] - read_output_values[1]
            explain = f'{p_opcode.name} : Modulos the values <b><span fgcolor="{YELLOW}">{read_output_values[0]}</span></b> and <b><span fgcolor="{YELLOW}">{read_output_values[1]}</span></b>'
        elif p_opcode == OPCODE.OP_HASH256:
            read_output_values = self.read_output_stack_params(1)
            h = hashlib.sha256()
            h.update(str.encode(read_output_values[0]))
            output = h.hexdigest()
            explain = f'{p_opcode.name} : SHA256 Hashes the value <b><span fgcolor="{YELLOW}">{read_output_values[0]}</span></b>'
        elif p_opcode == OPCODE.OP_HASH160:
            read_output_values = self.read_output_stack_params(1)
            output = hashlib.new("ripemd160", str.encode(read_output_values[0])).hexdigest()
            explain = f'{p_opcode.name} : RIPEMD160 Hashes the value <b><span fgcolor="{YELLOW}">{self.format_value_for_render(read_output_values[0])}</span></b>'
        elif p_opcode == OPCODE.OP_DUP:
            output = self.output_stack[-1]
            explain = f'{p_opcode.name} : Duplicates the value <b><span fgcolor="{YELLOW}">{self.format_value_for_render(output)}</span></b>'
        elif p_opcode == OPCODE.OP_DROP:
            read_output_values = self.read_output_stack_params(1)
            explain = f'{p_opcode.name} : Removes the last output value <b><span fgcolor="{YELLOW}">{self.format_value_for_render(read_output_values[0])}</span></b>'
        elif p_opcode == OPCODE.OP_VERIFY:
            read_output_values = self.read_output_stack_params(1)
            if read_output_values[0] != True:
                self.tx_invalid = True
                output = OPCODE.OP_VERIFY
                
            explain = f'{p_opcode.name} : Verifies if the last output value is <b><span fgcolor="{YELLOW}">True</span></b>'
        elif p_opcode == OPCODE.OP_EQUALVERIFY:
            read_output_values = self.read_output_stack_params(2)
            
            print("OP_EQUALVERIFY params : ", read_output_values)
            
            self.tx_invalid = read_output_values[0] != read_output_values[1]
            
            if self.tx_invalid:
                output = OPCODE.OP_EQUALVERIFY
        
            explain = f'{p_opcode.name} : Checks if <b><span fgcolor="{YELLOW}">{self.format_value_for_render(read_output_values[0])}</span></b> and <b><span fgcolor="{YELLOW}">{self.format_value_for_render(read_output_values[1])}</span></b> are equals. The transaction fails if they are not equals'
        elif p_opcode == OPCODE.OP_CHECKSIG:
            read_output_values = self.read_output_stack_params(2)
            
            print("OP_CHECKSIG params : ", read_output_values)
        
            # the payload is the stack without the sig
            payload = self.generate_sig_data(self.in_stack[1:])
            
            explain = f'{p_opcode.name} : Checks the signature for message <b><span fgcolor="{YELLOW}">{self.format_value_for_render(payload)}</span></b>'
            
            vk_hex = read_output_values[0]
            sig = read_output_values[1]

            verif_key = ecdsa.VerifyingKey.from_string(bytes.fromhex(vk_hex), curve=ecdsa.SECP256k1)
                        
            print("OP_CHECKSIG vk: ", verif_key.to_string("compressed").hex())
            print("OP_CHECKSIG sig: ", sig)

            try:
                verif_key.verify(bytes.fromhex(sig), payload, hashfunc=hashlib.sha256, sigdecode=sigdecode_der)
                output = True
            except ecdsa.BadSignatureError:
                print("Bad signature")
                output = False
        elif p_opcode == OPCODE.OP_IF:
            read_output_values = self.read_output_stack_params(1)
            if read_output_values[0] != 0:
                # enters a new block
                enter_next_input_block = True
                explain = f'{p_opcode.name} : Enters the IF block'
            else:
                explain = f'{p_opcode.name} : Does not enter the IF block'
        elif p_opcode == OPCODE.OP_ENDIF:
            # does nothing, no output
            explain = f'{p_opcode.name} : The current IF block ended'
        elif p_opcode == OPCODE.OP_RETURN:
            self.tx_invalid = True
            output = p_opcode
            explain = f'{p_opcode.name} : Automatically results in transaction fail'
        elif p_opcode == OPCODE.OP_CLTV:
            expire_time = self.output_stack[-1]
            
            if expire_time is None or expire_time < 0:
                self.tx_invalid = True
                self.tx_invalid_reason = f'The value is empty or less than 0'
            elif expire_time > tx_data["n_lock_time"]:
                self.tx_invalid = True
                self.tx_invalid_reason = f'The given expiry time {expire_time} is greater than nLockTime {tx_data["n_lock_time"]}'
            elif expire_time >= 500000000 and tx_data["n_lock_time"] < 500000000:
                self.tx_invalid = True
                self.tx_invalid_reason = f'The given expiry time is greater than 500000000 but nLockTime is less than 500000000'
            elif expire_time < 500000000 and tx_data["n_lock_time"] >= 500000000:
                self.tx_invalid = True
                self.tx_invalid_reason = f'The nLockTime is greater than 500000000 but given expiry time is less than 500000000'
            elif tx_data["n_lock_time"] == 0xFFFFFFFF:
                self.tx_invalid = True
                self.tx_invalid_reason = f'The nSequence is 0xFFFFFFFF'
                
            if self.tx_invalid:
                output = p_opcode
            
            explain = f'{p_opcode.name} : Check lock time for value <b><span fgcolor="{YELLOW}">{self.format_value_for_render(expire_time)}</span></b>, nLockTime of the transaction is <b><span fgcolor="{YELLOW}">{tx_data["n_lock_time"]}</span></b>'
        else:
            output = input_block[current_in_idx]
            explain = f'Reads the data <b><span fgcolor="{YELLOW}">{self.format_value_for_render(output)}</span></b> from input stack'

        if output is not None:
            self.output_stack.append(output)
            write_output_values.append(output)
            
        if explain is None:
            explain = f'Not handled OPCODE, got {p_opcode}, and input block {input_block}'

        return read_output_values, write_output_values, explain, enter_next_input_block
    
    def get_explain_for_push_value(self, opcode, value):
        if value == 0:
            value = "0 or False"
        if value == 1:
            value = "1 or True"
        return f'{opcode.name} : Pushes the value <b><span fgcolor="{YELLOW}">{value}</span></b>'
    
    def read_output_stack_params(self, nb_params):
        values = []
        for _ in range(nb_params):
            values.append(self.output_stack.pop())

        return values
    
    def generate_puzzle(self):
        script_sig_data = "satoshi"
        self.in_stack = [script_sig_data, OPCODE.OP_HASH256, "da2876b3eb31edb4436fa4650673fc6f01f90de2f1793c4ec332b2387b09726f", OPCODE.OP_EQUAL]
    
    def generate_p2pk_script(self):
        self.in_stack = [OPCODE.OP_CHECKSIG]
        
        sk = self.generate_secp256k1_keys()
        vk_hex = sk.verifying_key.to_string("compressed").hex()
        self.in_stack.insert(0, vk_hex)
        
        data = self.generate_sig_data(self.in_stack)
        sig = sk.sign(data, hashfunc=hashlib.sha256, sigencode=sigencode_der)
        sig_hex = sig.hex()
        self.in_stack.insert(0, sig_hex)

    def generate_p2pkh_script(self):
        self.in_stack = [OPCODE.OP_DUP, OPCODE.OP_HASH160]
        
        sk = self.generate_secp256k1_keys()
        vk_hex = sk.verifying_key.to_string("compressed").hex()
        self.in_stack.insert(0, vk_hex)
        
        vk_hash = hashlib.new("ripemd160", str.encode(vk_hex)).hexdigest()
        self.in_stack.extend([vk_hash, OPCODE.OP_EQUALVERIFY, OPCODE.OP_CHECKSIG])
        
        data = self.generate_sig_data(self.in_stack)
        sig = sk.sign(data, hashfunc=hashlib.sha256, sigencode=sigencode_der)
        sig_hex = sig.hex()
        self.in_stack.insert(0, sig_hex)
        
    def generate_freezing_funds(self):
        self.in_stack = [OPCODE.OP_CLTV, OPCODE.OP_DROP, OPCODE.OP_DUP, OPCODE.OP_HASH160]
        
        self.in_stack.insert(0, 2000) # expire time
        
        sk = self.generate_secp256k1_keys()
        vk_hex = sk.verifying_key.to_string("compressed").hex()
        self.in_stack.insert(0, vk_hex)
        
        vk_hash = hashlib.new("ripemd160", str.encode(vk_hex)).hexdigest()
        self.in_stack.extend([vk_hash, OPCODE.OP_EQUALVERIFY, OPCODE.OP_CHECKSIG])
        
        data = self.generate_sig_data(self.in_stack)
        sig = sk.sign(data, hashfunc=hashlib.sha256, sigencode=sigencode_der)
        sig_hex = sig.hex()
        self.in_stack.insert(0, sig_hex)
        
    def generate_secp256k1_keys(self):
        sk = ecdsa.SigningKey.generate(curve=ecdsa.SECP256k1)
        sk.to_der()
        return sk
        
    def generate_sig_data(self, payload):
        h = hashlib.sha256()
        h.update(str.encode(str(payload)))
        return str.encode(h.hexdigest())
    
    def format_value_for_render(self, value):
        if type(value) is str:
            if len(value) < 6:
                return value
            return value[0:3] + "..." + value[len(value) - 3:]
        
        try:
            return value.decode()[0:3] + "..." + value.decode()[len(value) - 3:]
        except (UnicodeDecodeError, AttributeError):
            return value