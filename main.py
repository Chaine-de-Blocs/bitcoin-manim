from manim import *
from enum import Enum

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
    OP_EQUAL = 135

class AnimOPCODESeq(Scene):
    def construct(self):
        # TODO check if stack valid
        in_stack = [OPCODE.OP_3, OPCODE.OP_3, OPCODE.OP_EQUAL]
        in_stack_mobj = []
        out_stack_mobj = []
        output_stack = []
        
        # Display the OPCODE input stack
        for idx, in_stack_value in enumerate(in_stack):
            opcode_text = MarkupText(f"{in_stack_value.name}").scale(0.6).to_corner(UL)
            if len(in_stack_mobj) > 0:
                opcode_text.next_to(in_stack_mobj[idx - 1], DOWN).align_to(in_stack_mobj[idx - 1], LEFT)
            self.play(Write(opcode_text))
            in_stack_mobj.append(opcode_text)
            
        # OP_1           1
        # OP_2           2
        # OP_EQUAL       False (1, 2) removed
        for idx, in_stack_value in enumerate(in_stack):
            new_output_stack = self.get_opcode_output_stack(
                p_opcode=in_stack_value,
                p_output_stack=output_stack.copy(),
                current_index=idx
            )
            
            output_text = MarkupText(f"{str(new_output_stack[len(new_output_stack) - 1])}").scale(0.6)
            
            if idx == 0:
                output_text.next_to(in_stack_mobj[idx], RIGHT)
            else:
                output_text.next_to(out_stack_mobj[idx - 1], DOWN).align_to(out_stack_mobj[idx - 1], LEFT)

            self.play(Indicate(in_stack_mobj[idx]))
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
            
            # TODO display what it does bottom right
        
        # Right part (50% screen) is split horizontally
        #   Top right = last result from stack
        #   Bottom right = explaination of the OPCODE
        # title = MarkupText(f"{in_stack[0].name}").scale(0.6).to_edge(LEFT + (UP + 0.1))
        # self.play(Write(title))
        # self.wait()
        # self.play(Indicate(title))
        
    def get_opcode_output_stack(self, p_opcode, p_output_stack, current_index):
        if p_opcode == OPCODE.OP_0 or p_opcode == OPCODE.OP_FALSE:
            p_output_stack.append(False)
        elif p_opcode == OPCODE.OP_1 or p_opcode == OPCODE.OP_TRUE:
            p_output_stack.append(True)
        elif p_opcode == OPCODE.OP_2 or p_opcode == OPCODE.OP_3: # TODO all numbers to 16
            p_output_stack.append(p_opcode.value - 80)
        elif p_opcode == OPCODE.OP_EQUAL:
            value_1 = p_output_stack[current_index - 2]
            value_2 = p_output_stack[current_index - 1]
            output = value_1 == value_2
            p_output_stack.pop()
            p_output_stack.pop()
            p_output_stack.append(output)

        return p_output_stack