otupy.validation.timing.TimingRecord
====================================

.. currentmodule:: otupy.validation.timing

.. autoclass:: TimingRecord
   :members:
   :show-inheritance:
   :inherited-members:
   :special-members: __init__, __call__, __add__, __mul__

   
   
   .. rubric:: Methods

   .. autosummary::
      :nosignatures:
   
      ~TimingRecord.stages_ms
   
   

   
   
   .. rubric:: Attributes

   .. autosummary::
   
      ~TimingRecord.cyclonedx_conversion_ms
      ~TimingRecord.final_processing_ms
      ~TimingRecord.http_prep_and_send_ms
      ~TimingRecord.network_to_actuator_ms
      ~TimingRecord.otupy_request_encoding_ms
      ~TimingRecord.otupy_response_decoding_ms
      ~TimingRecord.resource_discovery_ms
      ~TimingRecord.response_building_ms
      ~TimingRecord.response_network_ms
      ~TimingRecord.t1_5_request_encoded
      ~TimingRecord.t1_sendcmd_invoked
      ~TimingRecord.t2_packet_on_wire
      ~TimingRecord.t3_5_context_discovered
      ~TimingRecord.t3_actuator_update_start
      ~TimingRecord.t4_context_data_arrived
      ~TimingRecord.t5_actuator_response_ready
      ~TimingRecord.t6_5_response_decoded
      ~TimingRecord.t6_response_on_wire
      ~TimingRecord.t7_sendcmd_returned
      ~TimingRecord.total_round_trip_ms
   
   