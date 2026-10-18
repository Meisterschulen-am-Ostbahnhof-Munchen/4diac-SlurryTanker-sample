<?xml version="1.0" encoding="UTF-8"?>
<AdapterType Name="EVENT_HS_UNI_WSTRING" Comment="Handshake family, unidirectional fire-and-forget with WSTRING payload: REQ/REQD only, no reply">
	<Identification Standard="61499-1" Description="Copyright (c) 2026 HR Agrartechnik GmbH &#10; &#10;This program and the accompanying materials are made &#10;available under the terms of the Eclipse Public License 2.0 &#10;which is available at https://www.eclipse.org/legal/epl-2.0/ &#10; &#10;SPDX-License-Identifier: EPL-2.0">
	</Identification>
	<VersionInfo Organization="HR Agrartechnik GmbH" Version="1.0" Author="Franz Höpfinger" Date="2026-09-02" Remarks="Data-carrying variant of EVENT_HS_UNI: adds a WSTRING payload (REQD) to the fire-and-forget REQ, matching the 'name,value' message style (e.g. push,100) documented in HandshakePattern.md">
	</VersionInfo>
	<CompilerInfo packageName="adapter::types::bidirectional::Handshake">
	</CompilerInfo>
	<InterfaceList>
		<EventOutputs>
			<Event Name="REQ" Type="Event" Comment="Request/notification from Plug to Socket, no reply expected">
				<With Var="REQD"/>
			</Event>
		</EventOutputs>
		<OutputVars>
			<VarDeclaration Name="REQD" Type="WSTRING" Comment="Request payload, accompanies REQ"/>
		</OutputVars>
	</InterfaceList>
	<Service RightInterface="SOCKET" LeftInterface="PLUG">
		<ServiceSequence Name="notify">
			<ServiceTransaction>
				<InputPrimitive Interface="PLUG" Event="REQ" Parameters="REQD"/>
				<OutputPrimitive Interface="SOCKET" Event="REQ" Parameters="REQD"/>
			</ServiceTransaction>
		</ServiceSequence>
	</Service>
	<Attribute Name="eclipse4diac::core::TypeHash" Value="''"/>
	<Attribute Name="Documentation" Type="CDATA"><![CDATA[<p>Data-carrying variant of <code>EVENT_HS_UNI</code> (reduced,
unidirectional member of the <code>EVENT_HS</code> family, Handshake
design pattern, IEC 61499 primer course, Module 6, Valeriy Vyatkin).
Declares a single <b>REQ</b>/<b>REQD</b> event+payload pair, from Plug
to Socket - no <b>CNF</b>/<b>CNFD</b>, <b>IND</b>/<b>INDD</b>, or
<b>RSP</b>/<b>RSPD</b> at all.</p>
<p><b>This is deliberately not a real handshake</b>: the Socket side
has no way to acknowledge or refuse the request (or its payload), and
the Plug side has no way to know whether the Socket ever received or
reacted to it. Use this only for genuine fire-and-forget notifications
carrying a payload where that one-way, best-effort semantics is
actually acceptable.</p>
<p>Same Socket/Plug role split as <code>EVENT_HS</code>: <b>Plug</b>
(<code>Name&gt;&gt;</code>) keeps the declared direction and fires
REQ/REQD; <b>Socket</b> (<code>&gt;&gt;Name</code>) mirrors it and
reacts to REQ/REQD.</p>
<p>See <code>test_AX/Meins/DesingPatterns/HandshakePattern/HandshakePattern.md</code>
for the full write-up of the <code>EVENT_HS</code> family, including
this and the other three reduced variants (<code>EVENT_HS_UNI</code>,
<code>EVENT_HS_ACK</code>, <code>EVENT_HS_ACK_WSTRING</code>).</p>
<p>The <code>&lt;Service&gt;</code> block below is purely
documentation (a service-sequence diagram, per the XSD's
<code>minOccurs="0"</code> - optional, not required for the adapter
connection to actually forward events; the standard 4diac
<code>AE.adp</code> has none either). Added anyway since it does not
hurt and makes the single REQ transaction explicit.</p>
]]></Attribute>
</AdapterType>
