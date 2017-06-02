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
header_type ptp_t {
    fields {
        transportSpecific : 4;
        messageType       : 4;
        reserved          : 4;
        versionPTP        : 4;
        messageLength     : 16;
        domainNumber      : 8;
        reserved2         : 8;
        flags             : 16;
        correction        : 64;
        reserved3         : 32;
        sourcePortIdentity: 80;
        sequenceId        : 16;
        PTPcontrol        : 8;
        logMessagePeriod  : 8;
        originTimestamp   : 80;
    }
}
parser start { return parse_ethernet; }
header ethernet_t ethernet;

parser parse_ethernet {
    extract(ethernet);
    return select(latest.etherType) {
	ETHERTYPE_PTP: parse_ptp;
	default : ingress;

    }
}
header ptp_t ptp;

parser parse_ptp {
    extract(ptp);
    return select(latest.reserved2) {
	1       : parse_header_0;
	default : ingress;

    }
}
header_type header_0_t {
    fields {
		field_0 : 16;
		field_1 : 16;
		field_2 : 16;
		field_3 : 16;
		field_4 : 16;
		field_5 : 16;
		field_6 : 16;
		field_7 : 16;
		field_8 : 16;
		field_9 : 16;
		field_10: 16;
		field_11: 16;
		field_12: 16;
		field_13: 16;
		field_14: 16;
		field_15: 16;
		field_16: 16;
		field_17: 16;
		field_18: 16;
		field_19: 16;

    }
}
header header_0_t header_0;

parser parse_header_0 {
    extract(header_0);
    return select(latest.field_0) {
	default : ingress;

    }
}
action _nop() {

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
action mod_headers() {
	modify_field(header_0.field_0, 1);
	modify_field(header_0.field_1, header_0.field_0);
	modify_field(header_0.field_2, header_0.field_1);
	modify_field(header_0.field_3, header_0.field_2);
	modify_field(header_0.field_4, header_0.field_3);
	modify_field(header_0.field_5, header_0.field_4);
	modify_field(header_0.field_6, header_0.field_5);
	modify_field(header_0.field_7, header_0.field_6);
	modify_field(header_0.field_8, header_0.field_7);
	modify_field(header_0.field_9, header_0.field_8);
	modify_field(header_0.field_10, header_0.field_9);
	modify_field(header_0.field_11, header_0.field_10);
	modify_field(header_0.field_12, header_0.field_11);
	modify_field(header_0.field_13, header_0.field_12);
	modify_field(header_0.field_14, header_0.field_13);
	modify_field(header_0.field_15, header_0.field_14);
	modify_field(header_0.field_16, header_0.field_15);
	modify_field(header_0.field_17, header_0.field_16);
	modify_field(header_0.field_18, header_0.field_17);
	modify_field(header_0.field_19, header_0.field_18);

}
table test_tbl {
    reads {
        ptp.reserved2 : exact;
    } actions {
        		_nop;
		mod_headers;
    }
    size : 4;
}
control ingress {
    apply(forward_table);
    apply(test_tbl);

}
