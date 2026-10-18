<?xml version="1.0" encoding="UTF-8"?>
<AdapterType Name="EVENT_HS_UNI" Comment="Handshake family, unidirectional fire-and-forget (dataless): REQ only, no reply">
	<Identification Standard="61499-1" Description="Copyright (c) 2026 HR Agrartechnik GmbH &#10; &#10;This program and the accompanying materials are made &#10;available under the terms of the Eclipse Public License 2.0 &#10;which is available at https://www.eclipse.org/legal/epl-2.0/ &#10; &#10;SPDX-License-Identifier: EPL-2.0">
	</Identification>
	<VersionInfo Organization="HR Agrartechnik GmbH" Version="1.0" Author="Franz Höpfinger" Date="2026-09-02" Remarks="Unidirectional, dataless reduction of EVENT_HS: only REQ, no CNF/IND/RSP at all - a pure fire-and-forget notification, not a real handshake (no acknowledgement, no way to know the Socket side received it)">
	</VersionInfo>
	<CompilerInfo packageName="adapter::types::bidirectional::Handshake">
	</CompilerInfo>
	<InterfaceList>
		<EventOutputs>
			<Event Name="REQ" Type="Event" Comment="Request/notification from Plug to Socket, no reply expected">
			</Event>
		</EventOutputs>
	</InterfaceList>
	<Service RightInterface="SOCKET" LeftInterface="PLUG">
		<ServiceSequence Name="notify">
			<ServiceTransaction>
				<InputPrimitive Interface="PLUG" Event="REQ"/>
				<OutputPrimitive Interface="SOCKET" Event="REQ"/>
			</ServiceTransaction>
		</ServiceSequence>
	</Service>
	<Attribute Name="eclipse4diac::core::TypeHash" Value="''"/>
	<Attribute Name="Documentation" Type="CDATA"><![CDATA[<p>Reduced, unidirectional member of the <code>EVENT_HS</code> family
(Handshake design pattern, IEC 61499 primer course, Module 6, Valeriy
Vyatkin). Declares only a single <b>REQ</b> event, from Plug to
Socket - no <b>CNF</b>, <b>IND</b>, or <b>RSP</b> at all.</p>
<p><b>This is deliberately not a real handshake</b>: the Socket side
has no way to acknowledge or refuse the request, and the Plug side has
no way to know whether the Socket ever received or reacted to it. Use
this only for genuine fire-and-forget notifications where that
one-way, best-effort semantics is actually acceptable - not as a
drop-in replacement for <code>EVENT_HS</code>.</p>
<p>Same Socket/Plug role split as <code>EVENT_HS</code>: <b>Plug</b>
(<code>Name&gt;&gt;</code>) keeps the declared direction and fires
REQ; <b>Socket</b> (<code>&gt;&gt;Name</code>) mirrors it and reacts to
REQ.</p>
<p>See <code>test_AX/Meins/DesingPatterns/HandshakePattern/HandshakePattern.md</code>
for the full write-up of the <code>EVENT_HS</code> family, including
this and the other three reduced variants
(<code>EVENT_HS_UNI_WSTRING</code>, <code>EVENT_HS_ACK</code>,
<code>EVENT_HS_ACK_WSTRING</code>).</p>
<p>The <code>&lt;Service&gt;</code> block below is purely
documentation (a service-sequence diagram, per the XSD's
<code>minOccurs="0"</code> - optional, not required for the adapter
connection to actually forward events; the standard 4diac
<code>AE.adp</code> has none either). Added anyway since it does not
hurt and makes the single REQ transaction explicit.</p>
]]></Attribute>
</AdapterType>
