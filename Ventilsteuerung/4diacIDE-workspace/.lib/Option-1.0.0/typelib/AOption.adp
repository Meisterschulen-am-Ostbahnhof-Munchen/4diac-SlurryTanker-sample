<?xml version="1.0" encoding="UTF-8"?>
<AdapterType Name="AOption" Comment="Optionsmanagement-Adapter: INIT-Request/Confirm-Handshake mit QI (Event Input Qualifier, IEC 61499-1)">
	<Identification Standard="61499-1" Description="Copyright (c) 2026 Meisterschulen am Ostbahnhof&#10; &#10;This program and the accompanying materials are made&#10;available under the terms of the Eclipse Public License 2.0&#10;which is available at https://www.eclipse.org/legal/epl-2.0/&#10;&#10;SPDX-License-Identifier: EPL-2.0">
	</Identification>
	<VersionInfo Organization="Meisterschulen am Ostbahnhof" Version="1.0" Author="Franz Höpfinger" Date="2026-10-13" Remarks="initial API and implementation and/or initial documentation">
	</VersionInfo>
	<CompilerInfo packageName="Option">
	</CompilerInfo>
	<InterfaceList>
		<EventInputs>
			<Event Name="INIT_CNF" Type="Event" Comment="Initialisierung bestaetigt (SOCKET -&gt; PLUG)">
			</Event>
		</EventInputs>
		<EventOutputs>
			<Event Name="INIT_REQ" Type="Event" Comment="Initialisierung anfordern (PLUG -&gt; SOCKET)">
				<With Var="QI_OUT"/>
			</Event>
		</EventOutputs>
		<OutputVars>
			<VarDeclaration Name="QI_OUT" Type="BOOL" Comment="Event Input Qualifier zu INIT_REQ (IEC 61499-1): TRUE = Option anfordern/aktivieren (INIT_REQ+), FALSE = zurueckziehen/terminieren (INIT_REQ-)"/>
		</OutputVars>
	</InterfaceList>
	<Attribute Name="eclipse4diac::core::TypeHash" Value="''"/>
</AdapterType>
