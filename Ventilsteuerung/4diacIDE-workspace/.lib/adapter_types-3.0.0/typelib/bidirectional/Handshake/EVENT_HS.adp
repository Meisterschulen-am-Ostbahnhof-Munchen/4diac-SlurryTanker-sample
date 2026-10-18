<?xml version="1.0" encoding="UTF-8"?>
<AdapterType Name="EVENT_HS" Comment="Handshake pattern adapter interface (dataless): CNF/IND in, REQ/RSP out">
	<Identification Standard="61499-1" Description="Copyright (c) 2026 HR Agrartechnik GmbH &#10; &#10;This program and the accompanying materials are made &#10;available under the terms of the Eclipse Public License 2.0 &#10;which is available at https://www.eclipse.org/legal/epl-2.0/ &#10; &#10;SPDX-License-Identifier: EPL-2.0">
	</Identification>
	<VersionInfo Organization="HR Agrartechnik GmbH" Version="1.1" Author="Franz Höpfinger" Date="2026-08-31" Remarks="Swapped EventInputs/EventOutputs so the Plug plays the Requester role (fires REQ/RSP) and the Socket plays the Responder role (fires CNF/IND) - more natural left-to-right layout in the FBNetwork editor">
	</VersionInfo>
	<VersionInfo Organization="HR Agrartechnik GmbH" Version="1.0" Author="Franz Höpfinger" Date="2026-08-31" Remarks="Handshake design pattern (IEC 61499 primer course, Module 6, Valeriy Vyatkin), dataless variant as shown on slide 72 - initial version, Socket was the Requester">
	</VersionInfo>
	<CompilerInfo packageName="adapter::types::bidirectional::Handshake">
	</CompilerInfo>
	<InterfaceList>
		<EventInputs>
			<Event Name="CNF" Type="Event" Comment="Confirmation from Socket to Plug, answers a REQ">
			</Event>
			<Event Name="IND" Type="Event" Comment="Indication from Socket to Plug">
			</Event>
		</EventInputs>
		<EventOutputs>
			<Event Name="REQ" Type="Event" Comment="Request from Plug to Socket">
			</Event>
			<Event Name="RSP" Type="Event" Comment="Response from Plug to Socket, answers an IND">
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
		<ServiceSequence Name="indication_response">
			<ServiceTransaction>
				<InputPrimitive Interface="SOCKET" Event="IND"/>
				<OutputPrimitive Interface="PLUG" Event="IND"/>
			</ServiceTransaction>
			<ServiceTransaction>
				<InputPrimitive Interface="PLUG" Event="RSP"/>
				<OutputPrimitive Interface="SOCKET" Event="RSP"/>
			</ServiceTransaction>
		</ServiceSequence>
	</Service>
	<Attribute Name="eclipse4diac::core::TypeHash" Value="''"/>
	<Attribute Name="Documentation" Type="CDATA"><![CDATA[<p>Dataless adapter interface implementing the <b>Handshake design pattern</b>
(IEC 61499 primer course, Module 6 &ndash; Design methods and patterns,
Valeriy Vyatkin, Lule&aring; University of Technology / Aalto University,
slide 72, category <i>Behavioural</i>).</p>
<p>Bundles the classical Request/Confirm/Indication/Response service
primitives into a single adapter connection, instead of four separate
event connections between the two communication partners.</p>
<ul>
<li><b>REQ</b> &ndash; request from Plug to Socket ("please do X")</li>
<li><b>CNF</b> &ndash; confirmation from Socket to Plug, answers a REQ ("X done")</li>
<li><b>IND</b> &ndash; unsolicited indication from Socket to Plug ("something happened")</li>
<li><b>RSP</b> &ndash; response from Plug to Socket, answers an IND ("indication received")</li>
</ul>
<p><b>Plug</b> (<code>Name&gt;&gt;</code>) keeps the declared direction and
plays the <i>Requester/client</i> role: it fires REQ/RSP and reacts to
CNF/IND. <b>Socket</b> (<code>&gt;&gt;Name</code>) mirrors the direction
and plays the <i>Responder/server</i> role: it reacts to REQ/RSP and
fires CNF/IND.</p>
<p>Confirmed against the actual 4diac ECC compiler: it only checks that
<code>HS.&lt;Name&gt;</code> is some event declared on the adapter - it does
<b>not</b> check whether the direction makes sense at that Socket/Plug
side. Get the Sockets/Plugs declaration and the ECC wiring right on
purpose; a swapped/self-referential wiring will still validate.</p>
<p>This is the minimal, dataless variant exactly as shown on slide 72; no
payload variables are declared. See
<code>test_AX/Meins/DesingPatterns/HandshakePattern/HandshakePattern.md</code>
for the full write-up and usage examples.</p>
]]></Attribute>
</AdapterType>
