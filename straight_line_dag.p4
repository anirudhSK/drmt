#define ETHERTYPE_IPV4 0x0800
#define ETHERTYPE_PTP 0x088F7

#define TCP_PROTOCOL 0x06
#define UDP_PROTOCOL 0x11
#define GENERIC_PROTOCOL 0x9091
header_type ethernet_t {
    fields {
        dstAddr : 48;
        srcAddr : 48;
        etherType : 16;
    }
}
header ethernet_t ethernet;

parser start {
    return parse_ethernet;
}

parser parse_ethernet {
    extract(ethernet);
    return select(latest.etherType) {
        ETHERTYPE_IPV4 : parse_ipv4; 
        default : ingress;
    }
}
header_type ipv4_t {
    fields {
        version : 4;
        ihl : 4;
        diffserv : 8;
        totalLen : 16;
        identification : 16;
        flags : 3;
        fragOffset : 13;
        ttl : 8;
        protocol : 8;
        hdrChecksum : 16;
        srcAddr : 32;
        dstAddr : 32;
    }
}
header ipv4_t ipv4;

parser parse_ipv4 {
    extract(ipv4);
    return select(latest.protocol) {
        TCP_PROTOCOL : parse_tcp;
        UDP_PROTOCOL : parse_udp;
        default : ingress;
    }
}
header_type tcp_t {
    fields {
        srcPort : 16;
        dstPort : 16;
        seqNo : 32;
        ackNo : 32;
        dataOffset : 4;
        res : 3;
        ecn : 3;
        ctrl : 6;
        window : 16;
        checksum : 16;
        urgentPtr : 16;
    }
}
header tcp_t tcp;

parser parse_tcp {
    extract(tcp);
    return ingress;
}
header_type udp_t {
    fields {
        srcPort : 16;
        dstPort : 16;
        length_ : 16;
        checksum : 16;
    }
}
header udp_t udp;

parser parse_udp {
    extract(udp);
    return select(latest.dstPort) {
	default : ingress;

    }
}
action _drop() {
    drop();
}

action forward(port) {
    modify_field(standard_metadata.egress_spec, port);
}

table forward_table {
    reads {
        ethernet.dstAddr : exact;
    } actions {
        forward;
        _drop;
    }
    size : 4;
}
action _nop() {

}
action forward1(_port) {
modify_field(standard_metadata.egress_spec, _port);
}
table table_1 {
    reads {
        ethernet.dstAddr : exact;
    } actions {
        forward1;
    }
    size : 32;
}
action forward2(_port) {
modify_field(standard_metadata.egress_spec, _port);
}
table table_2 {
    reads {
        ethernet.dstAddr : exact;
    } actions {
        forward2;
    }
    size : 32;
}
action forward3(_port) {
modify_field(standard_metadata.egress_spec, _port);
}
table table_3 {
    reads {
        ethernet.dstAddr : exact;
    } actions {
        forward3;
    }
    size : 32;
}
action forward4(_port) {
modify_field(standard_metadata.egress_spec, _port);
}
table table_4 {
    reads {
        ethernet.dstAddr : exact;
    } actions {
        forward4;
    }
    size : 32;
}
action forward5(_port) {
modify_field(standard_metadata.egress_spec, _port);
}
table table_5 {
    reads {
        ethernet.dstAddr : exact;
    } actions {
        forward5;
    }
    size : 32;
}
action forward6(_port) {
modify_field(standard_metadata.egress_spec, _port);
}
table table_6 {
    reads {
        ethernet.dstAddr : exact;
    } actions {
        forward6;
    }
    size : 32;
}
action forward7(_port) {
modify_field(standard_metadata.egress_spec, _port);
}
table table_7 {
    reads {
        ethernet.dstAddr : exact;
    } actions {
        forward7;
    }
    size : 32;
}
action forward8(_port) {
modify_field(standard_metadata.egress_spec, _port);
}
table table_8 {
    reads {
        ethernet.dstAddr : exact;
    } actions {
        forward8;
    }
    size : 32;
}
action forward9(_port) {
modify_field(standard_metadata.egress_spec, _port);
}
table table_9 {
    reads {
        ethernet.dstAddr : exact;
    } actions {
        forward9;
    }
    size : 32;
}
action forward10(_port) {
modify_field(standard_metadata.egress_spec, _port);
}
table table_10 {
    reads {
        ethernet.dstAddr : exact;
    } actions {
        forward10;
    }
    size : 32;
}
action forward11(_port) {
modify_field(standard_metadata.egress_spec, _port);
}
table table_11 {
    reads {
        ethernet.dstAddr : exact;
    } actions {
        forward11;
    }
    size : 32;
}
action forward12(_port) {
modify_field(standard_metadata.egress_spec, _port);
}
table table_12 {
    reads {
        ethernet.dstAddr : exact;
    } actions {
        forward12;
    }
    size : 32;
}
action forward13(_port) {
modify_field(standard_metadata.egress_spec, _port);
}
table table_13 {
    reads {
        ethernet.dstAddr : exact;
    } actions {
        forward13;
    }
    size : 32;
}
action forward14(_port) {
modify_field(standard_metadata.egress_spec, _port);
}
table table_14 {
    reads {
        ethernet.dstAddr : exact;
    } actions {
        forward14;
    }
    size : 32;
}
action forward15(_port) {
modify_field(standard_metadata.egress_spec, _port);
}
table table_15 {
    reads {
        ethernet.dstAddr : exact;
    } actions {
        forward15;
    }
    size : 32;
}
action forward16(_port) {
modify_field(standard_metadata.egress_spec, _port);
}
table table_16 {
    reads {
        ethernet.dstAddr : exact;
    } actions {
        forward16;
    }
    size : 32;
}
action forward17(_port) {
modify_field(standard_metadata.egress_spec, _port);
}
table table_17 {
    reads {
        ethernet.dstAddr : exact;
    } actions {
        forward17;
    }
    size : 32;
}
action forward18(_port) {
modify_field(standard_metadata.egress_spec, _port);
}
table table_18 {
    reads {
        ethernet.dstAddr : exact;
    } actions {
        forward18;
    }
    size : 32;
}
action forward19(_port) {
modify_field(standard_metadata.egress_spec, _port);
}
table table_19 {
    reads {
        ethernet.dstAddr : exact;
    } actions {
        forward19;
    }
    size : 32;
}
control ingress {
    apply(forward_table);
    apply(table_1);
	apply(table_2);
	apply(table_3);
	apply(table_4);
	apply(table_5);
	apply(table_6);
	apply(table_7);
	apply(table_8);
	apply(table_9);
	apply(table_10);
	apply(table_11);
	apply(table_12);
	apply(table_13);
	apply(table_14);
	apply(table_15);
	apply(table_16);
	apply(table_17);
	apply(table_18);
	apply(table_19);
	
}
