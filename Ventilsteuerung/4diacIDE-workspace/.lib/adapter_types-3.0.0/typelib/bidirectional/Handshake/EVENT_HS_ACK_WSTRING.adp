<?xml version="1.0" encoding="UTF-8"?>
<AdapterType Name="EVENT_HS_ACK_WSTRING" Comment="Handshake family, request/confirm with WSTRING payload: CNF/CNFD in, REQ/REQD out, no IND/RSP">
	<Identification Standard="61499-1" Description="Copyright (c) 2026 HR Agrartechnik GmbH &#10; &#10;This program and the accompanying materials are made &#10;available under the terms of the Eclipse Public License 2.0 &#10;which is available at https://www.eclipse.org/legal/epl-2.0/ &#10; &#10;SPDX-License-Identifier: EPL-2.0">
	</Identification>
	<VersionInfo Organization="HR Agrartechnik GmbH" Version="1.0" Author="Franz Höpfinger" Date="2026-09-02" Remarks="Data-carrying variant of EVENT_HS_ACK: adds WSTRING payloads (REQD/CNFD) to the request/confirm pair, matching the 'name,value' message style (e.g. push,100) documented in HandshakePattern.md">
	</VersionInfo>
	<CompilerInfo packageName="adapter::types::bidirectional::Handshake">
	</CompilerInfo>
	<InterfaceList>
		<EventInputs>
			<Event Name="CNF" Type="Event" Comment="Confirmation from Socket to Plug, answers a REQ">
				<With Var="CNFD"/>
			</Event>
		</EventInputs>
		<EventOutputs>
			<Event Name="REQ" Type="Event" Comment="Request from Plug to Socket">
				<With Var="REQD"/>
			</Event>
		</EventOutputs>
		<InputVars>
			<VarDeclaration Name="CNFD" Type="WSTRING" Comment="Confirmation payload, accompanies CNF"/>
		</InputVars>
		<OutputVars>
			<VarDeclaration Name="REQD" Type="WSTRING" Comment="Request payload, accompanies REQ"/>
		</OutputVars>
	</InterfaceList>
	<Service RightInterface="SOCKET" LeftInterface="PLUG">
		<ServiceSequence Name="request_confirm">
			<ServiceTransaction>
				<InputPrimitive Interface="PLUG" Event="REQ" Parameters="REQD"/>
				<OutputPrimitive Interface="SOCKET" Event="REQ" Parameters="REQD"/>
			</ServiceTransaction>
			<ServiceTransaction>
				<InputPrimitive Interface="SOCKET" Event="CNF" Parameters="CNFD"/>
				<OutputPrimitive Interface="PLUG" Event="CNF" Parameters="CNFD"/>
			</ServiceTransaction>
		</ServiceSequence>
	</Service>
	<Attribute Name="eclipse4diac::core::TypeHash" Value="''"/>
	<Attribute Name="Documentation" Type="CDATA"><![CDATA[<p>Data-carrying variant of <code>EVENT_HS_ACK</code> (reduced member
of the <code>EVENT_HS</code> family, Handshake design pattern,
IEC 61499 primer course, Module 6, Valeriy Vyatkin), keeping only the
request/confirm half of the full REQ/CNF/IND/RSP vocabulary, each with
a <code>WSTRING</code> payload:</p>
<ul>
<li><b>REQ</b> / <b>REQD</b> &ndash; request + payload, from Plug to Socket (e.g. <code>"push,100"</code>)</li>
<li><b>CNF</b> / <b>CNFD</b> &ndash; confirmation + payload, from Socket to Plug, answers a REQ (e.g. <code>"push,100"</code>)</li>
</ul>
<p>No <b>IND</b>/<b>RSP</b> (and no <b>INDD</b>/<b>RSPD</b>): the
Socket side can only ever answer a REQ with a CNF, it can never push
an unsolicited indication back to the Plug.</p>
<p>Same Socket/Plug role split as <code>EVENT_HS</code>: <b>Plug</b>
(<code>Name&gt;&gt;</code>) keeps the declared direction and plays the
<i>Requester/client</i> role: it fires REQ/REQD and reacts to
CNF/CNFD. <b>Socket</b> (<code>&gt;&gt;Name</code>) mirrors the
direction and plays the <i>Responder/server</i> role: it reacts to
REQ/REQD and fires CNF/CNFD.</p>
<p>See <code>test_AX/Meins/DesingPatterns/HandshakePattern/HandshakePattern.md</code>
for the full write-up of the <code>EVENT_HS</code> family, including
this and the other three reduced variants (<code>EVENT_HS_UNI</code>,
<code>EVENT_HS_UNI_WSTRING</code>, <code>EVENT_HS_ACK</code>).</p>
]]></Attribute>
</AdapterType>
