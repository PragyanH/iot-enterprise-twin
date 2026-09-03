@load policy/tuning/json-logs

module Aegis;

export {
    redef enum Log::ID += { LOG };
    const target: addr = 192.168.56.20 &redef;

    type Info: record {
        ts: time &log;
        syn: count &log;
        syn_ack: count &log;
        ack: count &log;
        incomplete_ratio: double &log;
        handshake_completion_ratio: double &log;
        unique_sources: count &log;
        unique_destination_ports: count &log;
        orig_packets: count &log;
        resp_packets: count &log;
        mean_packet_size: double &log;
        mean_iat: double &log;
        flow_symmetry: double &log;
    };
}

global syn_count: count = 0;
global syn_ack_count: count = 0;
global ack_count: count = 0;
global orig_packet_count: count = 0;
global resp_packet_count: count = 0;
global total_bytes: count = 0;
global sources: set[addr];
global destination_ports: set[port];

function emit_window()
    {
    local incomplete = syn_count > 0 ? (syn_count - min(syn_count, syn_ack_count)) * 1.0 / syn_count : 0.0;
    local completion = syn_count > 0 ? min(syn_count, syn_ack_count) * 1.0 / syn_count : 1.0;
    local total_packets = orig_packet_count + resp_packet_count;
    local symmetry = orig_packet_count > 0 ? min(orig_packet_count, resp_packet_count) * 1.0 / max(orig_packet_count, resp_packet_count) : 1.0;
    Log::write(LOG, [$ts=network_time(), $syn=syn_count, $syn_ack=syn_ack_count,
        $ack=ack_count, $incomplete_ratio=incomplete,
        $handshake_completion_ratio=completion, $unique_sources=|sources|,
        $unique_destination_ports=|destination_ports|, $orig_packets=orig_packet_count,
        $resp_packets=resp_packet_count,
        $mean_packet_size=total_packets > 0 ? total_bytes * 1.0 / total_packets : 0.0,
        $mean_iat=total_packets > 0 ? 1.0 / total_packets : 1.0,
        $flow_symmetry=symmetry]);
    syn_count = 0;
    syn_ack_count = 0;
    ack_count = 0;
    orig_packet_count = 0;
    resp_packet_count = 0;
    total_bytes = 0;
    sources = set();
    destination_ports = set();
    schedule 1sec { emit_window() };
    }

event zeek_init()
    {
    Log::create_stream(LOG, [$columns=Info, $path="aegis_live"]);
    schedule 1sec { emit_window() };
    }

event tcp_packet(c: connection, is_orig: bool, flags: string, seq: count, ack: count, len: count, payload: string)
    {
    if ( c$id$resp_h != target )
        return;
    add sources[c$id$orig_h];
    add destination_ports[c$id$resp_p];
    total_bytes += len;
    if ( is_orig )
        orig_packet_count += 1;
    else
        resp_packet_count += 1;
    if ( flags == "S" )
        syn_count += 1;
    else if ( flags == "SA" )
        syn_ack_count += 1;
    else if ( flags == "A" )
        ack_count += 1;
    }
