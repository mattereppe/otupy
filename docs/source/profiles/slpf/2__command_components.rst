2. Command Components
=====================

.. list-table:: Active SLPF command matrix
   :header-rows: 1

   * - Action
     - Target(s)
     - Accepted arguments
   * - ``query``
     - ``features``
     - ``response_requested``
   * - ``allow``
     - ``ipv4_connection``, ``ipv4_net``
     - ``response_requested``, ``start_time``, ``stop_time``, ``duration``, ``persistent``, ``direction``, ``insert_rule``, ``drop_process``
   * - ``deny``
     - ``ipv4_connection``, ``ipv4_net``
     - Same as ``allow``
   * - ``update``
     - ``file``
     - ``response_requested``, ``start_time``
   * - ``delete``
     - ``slpf:rule_number``
     - ``response_requested``, ``start_time``

SLPF-specific arguments are ``drop_process``, ``persistent``, ``direction``,
and ``insert_rule``. The actuator selector can contain ``hostname``,
``named_group``, ``asset_id``, and ``asset_tuple``.
