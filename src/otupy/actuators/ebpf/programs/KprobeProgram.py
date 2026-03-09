from bcc import BPF
from otupy.actuators.ebpf.base.ebpf_base import BaseEBPFProgram


class KprobeProgram(BaseEBPFProgram):

    def __init__(self, prog_path=None, section=None, function=None, **kwargs):
        super().__init__(**kwargs)

        self.prog_path = prog_path
        self.section = section
        self.function = function

        self.bpf = None


    def load(self, **kwargs):

        if not self.prog_path or not self.section or not self.function:
            raise ValueError("prog_path, section and function are required")

        self.bpf = BPF(src_file=self.prog_path)

        self.bpf.attach_kprobe(
            event=self.function,
            fn_name=self.section
        )


    def remove(self, **kwargs):

        if self.bpf:
            self.bpf.detach_kprobe(self.function)


    def query(self, **kwargs):

        return [{
            "file": self.prog_path,
            "section": self.section,
            "function": self.function,
            "attach_type": "kprobe"
        }]