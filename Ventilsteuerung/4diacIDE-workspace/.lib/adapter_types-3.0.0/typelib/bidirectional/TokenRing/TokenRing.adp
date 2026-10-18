<?xml version="1.0" encoding="UTF-8"?>
<AdapterType Name="TokenRing" Comment="Mutual Exclusion pattern adapter interface (dataless): RCV in, GIVE out">
	<Identification Standard="61499-1" Description="Copyright (c) 2026 HR Agrartechnik GmbH &#10; &#10;This program and the accompanying materials are made &#10;available under the terms of the Eclipse Public License 2.0 &#10;which is available at https://www.eclipse.org/legal/epl-2.0/ &#10; &#10;SPDX-License-Identifier: EPL-2.0">
	</Identification>
	<VersionInfo Organization="HR Agrartechnik GmbH" Version="1.1" Author="Franz Höpfinger" Date="2026-08-31" Remarks="GIVE/RCV Socket/Plug roles confirmed against the primary source: Dai/Vyatkin/Christensen/Dubinin, 'Function Block Implementation of Service Oriented Architecture: Case Study', IEEE INDIN 2014 - Section III.B: 'an adapter input MTXIN and output MTXOUT are reserved'">
	</VersionInfo>
	<VersionInfo Organization="HR Agrartechnik GmbH" Version="1.0" Author="Franz Höpfinger" Date="2026-08-31" Remarks="Mutual Exclusion / TokenRing design pattern (IEC 61499 primer course, Module 6, Valeriy Vyatkin, slide 15), initial version">
	</VersionInfo>
	<CompilerInfo packageName="adapter::types::bidirectional::TokenRing">
	</CompilerInfo>
	<InterfaceList>
		<EventInputs>
			<Event Name="RCV" Type="Event" Comment="Acknowledgement from Socket that it received the token, sent back to Plug">
			</Event>
		</EventInputs>
		<EventOutputs>
			<Event Name="GIVE" Type="Event" Comment="Plug hands the token to Socket">
			</Event>
		</EventOutputs>
	</InterfaceList>
	<Service RightInterface="SOCKET" LeftInterface="PLUG">
		<ServiceSequence Name="token_pass">
			<ServiceTransaction>
				<InputPrimitive Interface="PLUG" Event="GIVE"/>
				<OutputPrimitive Interface="SOCKET" Event="GIVE"/>
			</ServiceTransaction>
			<ServiceTransaction>
				<InputPrimitive Interface="SOCKET" Event="RCV"/>
				<OutputPrimitive Interface="PLUG" Event="RCV"/>
			</ServiceTransaction>
		</ServiceSequence>
	</Service>
	<Attribute Name="eclipse4diac::core::TypeHash" Value="''"/>
	<Attribute Name="Documentation" Type="CDATA"><![CDATA[<p>Dataless adapter interface implementing the <b>TokenRing / Mutual
Exclusion design pattern</b> (IEC 61499 primer course, Module 6,
Valeriy Vyatkin, slide 15). Used to pass a mutual-exclusion "token"
around a ring of controllers that share a resource: only the current
token holder may enter its critical section; when done, it passes the
token to its neighbour.</p>
<ul>
<li><b>GIVE</b> &ndash; from Plug to Socket: hand the token to the neighbour</li>
<li><b>RCV</b> &ndash; from Socket to Plug: acknowledge that the token was received</li>
</ul>
<p><b>Plug</b> (<code>Name&gt;&gt;</code>, named <code>MTXOUT</code> in
the source) plays the "giver" role: fires <b>GIVE</b>, reacts to
<b>RCV</b>. <b>Socket</b> (<code>&gt;&gt;Name</code>, named
<code>MTXIN</code>) plays the "receiver" role: reacts to <b>GIVE</b>,
fires <b>RCV</b>. A controller in the ring needs <b>two</b> instances -
one <code>MTXOUT</code> (Plug) towards its downstream neighbour, one
<code>MTXIN</code> (Socket) towards its upstream neighbour.</p>
<p>Source: W. Dai, V. Vyatkin, J. H. Christensen, V. Dubinin, "Function
Block Implementation of Service Oriented Architecture: Case Study,"
IEEE INDIN 2014, Section III.B/IV.A and Fig. 7/10 (local file
<code>INDIN14_DVCD.pdf</code>) - confirms "an adapter input MTXIN and
output MTXOUT are reserved" and that MTXIN/MTXOUT are wired into a ring
to implement mutually exclusive access. See
<code>test_AX/Meins/DesingPatterns/TokenRingPattern/TokenRingPattern.md</code>
for the full write-up.</p>
]]></Attribute>
</AdapterType>
