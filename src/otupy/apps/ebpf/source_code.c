const char *bpf_source = R"(
#include <uapi/linux/ptrace.h>
#include <linux/sched.h>

// Definiamo una mappa per inviare gli eventi allo user-space
// TYPE: BPF_MAP_TYPE_PERF_EVENT_ARRAY (usato per i flussi di eventi)
struct {
    __uint(type, BPF_MAP_TYPE_PERF_EVENT_ARRAY);
    __uint(key_size, sizeof(int));
    __uint(value_size, sizeof(u32));
} events SEC(".maps");

// Definizione della struttura dell'evento che vogliamo inviare
struct data_t {
    pid_t pid;
    char comm[TASK_COMM_LEN];
};

// Funzione eBPF che viene eseguita all'entrata della syscall execve
int syscall__execve(struct pt_regs *ctx) {
    struct data_t data = {};
    
    // Otteniamo il PID e il nome del processo
    data.pid = bpf_get_current_pid_tgid();
    bpf_get_current_comm(&data.comm, sizeof(data.comm));

    // Invia i dati allo user-space tramite il perf buffer
    bpf_perf_event_output(ctx, &events, BPF_F_CURRENT_CPU, &data, sizeof(data));

    return 0;
}
)";