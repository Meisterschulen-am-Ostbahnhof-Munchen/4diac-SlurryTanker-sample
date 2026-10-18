<?xml version="1.0" encoding="UTF-8"?>
<AdapterType Name="EVENT_HS_ACK" Comment="Handshake family, request/confirm only (dataless): CNF in, REQ out, no IND/RSP">
	<Identification Standard="61499-1" Description="Copyright (c) 2026 HR Agrartechnik GmbH &#10; &#10;This program and the accompanying materials are made &#10;available under the terms of the Eclipse Public License 2.0 &#10;which is available at https://www.eclipse.org/legal/epl-2.0/ &#10; &#10;SPDX-License-Identifier: EPL-2.0">
	</Identification>
	<VersionInfo Organization="HR Agrartechnik GmbH" Version="1.0" Author="Franz Höpfinger" Date="2026-09-02" Remarks="Reduction of EVENT_HS to just the request/confirm half: REQ/CNF, no IND/RSP - use when the Socket side never needs to send unsolicited indications back to the Plug">
	</VersionInfo>
	<CompilerInfo packageName="adapter::types::bidirectional::Handshake">
	</CompilerInfo>
	<InterfaceList>
		<EventInputs>
			<Event Name="CNF" Type="Event" Comment="Confirmation from Socket to Plug, answers a REQ">
			</Event>
		</EventInputs>
		<EventOutputs>
			<Event Name="REQ" Type="Event" Comment="Request from Plug to Socket">
			</Event>
		</EventOutputs>
	</InterfaceList>
	<Service RightInterface="SOCKET" LeftInterface="PLUG">
		<ServiceSequence Name="request_confirm">
			<ServiceTransaction>
				<InputPrimitive Interface="PLUG" Event="REQ"/>
				<OutputPrimitive Interface="SOCKET" Event="REQ"/>
			</ServiceTransaction>
			<ServiceTransaction>
				<InputPrimitive Interface="SOCKET" Event="CNF"/>
				<OutputPrimitive Interface="PLUG" Event="CNF"/>
			</ServiceTransaction>
		</ServiceSequence>
	</Service>
	<Attribute Name="eclipse4diac::core::TypeHash" Value="''"/>
	<Attribute Name="Documentation" Type="CDATA"><![CDATA[<p>Reduced member of the <code>EVENT_HS</code> family (Handshake
design pattern, IEC 61499 primer course, Module 6, Valeriy Vyatkin)
that keeps only the request/confirm half of the full REQ/CNF/IND/RSP
vocabulary:</p>
<ul>
<li><b>REQ</b> &ndash; request from Plug to Socket ("please do X")</li>
<li><b>CNF</b> &ndash; confirmation from Socket to Plug, answers a REQ ("X done")</li>
</ul>
<p>No <b>IND</b>/<b>RSP</b>: the Socket side can only ever answer a
REQ, it can never push an unsolicited indication back to the Plug.
This is a real (if one-directional-per-transaction) handshake, unlike
<code>EVENT_HS_UNI</code> - every REQ does get a CNF.</p>
<p>Same Socket/Plug role split as <code>EVENT_HS</code>: <b>Plug</b>
(<code>Name&gt;&gt;</code>) keeps the declared direction and plays the
<i>Requester/client</i> role: it fires REQ and reacts to CNF.
<b>Socket</b> (<code>&gt;&gt;Name</code>) mirrors the direction and
plays the <i>Responder/server</i> role: it reacts to REQ and fires
CNF.</p>
<p>See <code>test_AX/Meins/DesingPatterns/HandshakePattern/HandshakePattern.md</code>
for the full write-up of the <code>EVENT_HS</code> family, including
this and the other three reduced variants (<code>EVENT_HS_UNI</code>,
<code>EVENT_HS_UNI_WSTRING</code>, <code>EVENT_HS_ACK_WSTRING</code>).</p>
]]></Attribute>
</AdapterType>
