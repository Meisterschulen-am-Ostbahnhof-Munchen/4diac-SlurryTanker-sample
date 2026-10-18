<?xml version="1.0" encoding="UTF-8"?>
<AdapterType Name="ASR_AX" Comment="bidirectional Adapter Interface for 2 Events (forward, Set/Reset) and 1 Bool (backward, AX-style)">
	<Identification Standard="61499-1" Description="Copyright (c) 2026 HR Agrartechnik GmbH &#10; &#10;This program and the accompanying materials are made &#10;available under the terms of the Eclipse Public License 2.0 &#10;which is available at https://www.eclipse.org/legal/epl-2.0/ &#10; &#10;SPDX-License-Identifier: EPL-2.0">
	</Identification>
	<VersionInfo Organization="HR Agrartechnik GmbH" Version="1.0" Author="Franz Höpfinger" Date="2026-09-03" Remarks="Initial Version">
	</VersionInfo>
	<CompilerInfo packageName="adapter::types::bidirectional">
	</CompilerInfo>
	<InterfaceList>
		<EventInputs>
			<Event Name="EI1" Type="Event" Comment="Indication (or Request)">
				<With Var="DI1"/>
			</Event>
		</EventInputs>
		<EventOutputs>
			<Event Name="SET" Type="Event" Comment="Set / Switch on">
			</Event>
			<Event Name="RESET" Type="Event" Comment="Reset / Switch off">
			</Event>
		</EventOutputs>
		<InputVars>
			<VarDeclaration Name="DI1" Type="BOOL" Comment="Indication (or Request) Data to Plug"/>
		</InputVars>
	</InterfaceList>
	<Attribute Name="eclipse4diac::core::TypeHash" Value="''"/>
</AdapterType>
