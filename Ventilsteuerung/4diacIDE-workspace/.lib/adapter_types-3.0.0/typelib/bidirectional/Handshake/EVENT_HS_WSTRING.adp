<?xml version="1.0" encoding="UTF-8"?>
<AdapterType Name="EVENT_HS_WSTRING" Comment="Handshake pattern adapter interface with WSTRING payload: CNF/IND in, REQ/RSP out">
	<Identification Standard="61499-1" Description="Copyright (c) 2026 HR Agrartechnik GmbH &#10; &#10;This program and the accompanying materials are made &#10;available under the terms of the Eclipse Public License 2.0 &#10;which is available at https://www.eclipse.org/legal/epl-2.0/ &#10; &#10;SPDX-License-Identifier: EPL-2.0">
	</Identification>
	<VersionInfo Organization="HR Agrartechnik GmbH" Version="1.0" Author="Franz Höpfinger" Date="2026-08-31" Remarks="Data-carrying variant of EVENT_HS, matching Vyatkin's own 'service' adapter (Module 6, slide 48): same REQ/CNF/IND/RSP events, plus a WSTRING payload per event, exactly like the 'push,100' style messages in the slide's message-sequence examples (slide 42)">
	</VersionInfo>
	<CompilerInfo packageName="adapter::types::bidirectional::Handshake">
	</CompilerInfo>
	<InterfaceList>
		<EventInputs>
			<Event Name="CNF" Type="Event" Comment="Confirmation from Socket to Plug, answers a REQ">
				<With Var="CNFD"/>
			</Event>
			<Event Name="IND" Type="Event" Comment="Indication from Socket to Plug">
				<With Var="INDD"/>
			</Event>
		</EventInputs>
		<EventOutputs>
			<Event Name="REQ" Type="Event" Comment="Request from Plug to Socket">
				<With Var="REQD"/>
			</Event>
			<Event Name="RSP" Type="Event" Comment="Response from Plug to Socket, answers an IND">
				<With Var="RSPD"/>
			</Event>
		</EventOutputs>
		<InputVars>
			<VarDeclaration Name="CNFD" Type="WSTRING" Comment="Confirmation payload, accompanies CNF"/>
			<VarDeclaration Name="INDD" Type="WSTRING" Comment="Indication payload, accompanies IND"/>
		</InputVars>
		<OutputVars>
			<VarDeclaration Name="REQD" Type="WSTRING" Comment="Request payload, accompanies REQ"/>
			<VarDeclaration Name="RSPD" Type="WSTRING" Comment="Response payload, accompanies RSP"/>
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
		<ServiceSequence Name="indication_response">
			<ServiceTransaction>
				<InputPrimitive Interface="SOCKET" Event="IND" Parameters="INDD"/>
				<OutputPrimitive Interface="PLUG" Event="IND" Parameters="INDD"/>
			</ServiceTransaction>
			<ServiceTransaction>
				<InputPrimitive Interface="PLUG" Event="RSP" Parameters="RSPD"/>
				<OutputPrimitive Interface="SOCKET" Event="RSP" Parameters="RSPD"/>
			</ServiceTransaction>
		</ServiceSequence>
	</Service>
	<Attribute Name="eclipse4diac::core::TypeHash" Value="''"/>
	<Attribute Name="Documentation" Type="CDATA"><![CDATA[<p>Data-carrying variant of the <b>Handshake design pattern</b> adapter
(IEC 61499 primer course, Module 6 &ndash; Design methods and patterns,
Valeriy Vyatkin). Same REQ/CNF/IND/RSP event vocabulary as
<code>EVENT_HS</code>, but each event carries a <code>WSTRING</code>
payload &ndash; matching Vyatkin's own generic <i>"service"</i> adapter
(slide 48), used throughout the Service-Oriented-Architecture part of
the course for both service-requester and plant/process-data
interfaces.</p>
<ul>
<li><b>REQ</b> / <b>REQD</b> &ndash; request + payload, from Plug to Socket (e.g. <code>"push,100"</code>)</li>
<li><b>CNF</b> / <b>CNFD</b> &ndash; confirmation + payload, from Socket to Plug, answers a REQ</li>
<li><b>IND</b> / <b>INDD</b> &ndash; unsolicited indication + payload, from Socket to Plug</li>
<li><b>RSP</b> / <b>RSPD</b> &ndash; response + payload, from Plug to Socket, answers an IND</li>
</ul>
<p>Same Socket/Plug role split as <code>EVENT_HS</code>: <b>Plug</b>
(<code>Name&gt;&gt;</code>) plays the Requester/client role (fires
REQ/RSP, reacts to CNF/IND); <b>Socket</b> (<code>&gt;&gt;Name</code>)
plays the Responder/server role (reacts to REQ/RSP, fires CNF/IND).</p>
<p>See <code>test_AX/Meins/DesingPatterns/HandshakePattern/HandshakePattern.md</code>
for the full write-up; use this variant instead of the dataless
<code>EVENT_HS</code> when an actual payload needs to travel with the
handshake. The payload type is fixed at WSTRING for now and can be
swapped for a more specific/typed adapter later if needed.</p>
]]></Attribute>
</AdapterType>
