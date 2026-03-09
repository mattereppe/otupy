from otupy.apps.ebpf.base_producer import BaseEBPFProducer
from otupy.apps.ebpf.decorators import producer_plugin
from otupy.apps.ebpf.utils import handle_response
from otupy import Command
from otupy.profiles.ebpf.actuator import Specifiers
import otupy as oc2


@producer_plugin("tc")
class TCProducer(BaseEBPFProducer):

    def load(self, producer: oc2.Producer, target, asset_id: str):

        actuator_spec = Specifiers({"asset_id": asset_id})
        cmd = Command(
            action=oc2.Actions.create,
            target=target,
            actuator=actuator_spec
        )

        resp = producer.sendcmd(cmd)
        return handle_response(resp)


    def delete(self, producer: oc2.Producer, target, asset_id: str):

        actuator_spec = Specifiers({"asset_id": asset_id})
        cmd = Command(
            action=oc2.Actions.delete,
            target=target,
            actuator=actuator_spec
        )

        resp = producer.sendcmd(cmd)
        return handle_response(resp)


    def query(self, producer: oc2.Producer, target, asset_id: str):

        actuator_spec = Specifiers({"asset_id": asset_id})
        cmd = Command(
            action=oc2.Actions.query,
            target=target,
            actuator=actuator_spec
        )

        resp = producer.sendcmd(cmd)
        return handle_response(resp)