<?xml version="1.0" encoding="UTF-8"?>
<AdapterType Name="ASRT" Comment="unidirectional Adapter Interface for 3 Events">
	<Identification Standard="61499-1" Description="Copyright (c) 2026 HR Agrartechnik GmbH &#10; &#10;This program and the accompanying materials are made &#10;available under the terms of the Eclipse Public License 2.0 &#10;which is available at https://www.eclipse.org/legal/epl-2.0/ &#10; &#10;SPDX-License-Identifier: EPL-2.0">
	</Identification>
	<VersionInfo Organization="HR Agrartechnik GmbH" Version="1.0" Author="Franz Höpfinger" Date="2026-09-03" Remarks="Initial Version, wie ASR (2 Events) aber mit TOGGLE, fuer AX_T_FF_SR">
	</VersionInfo>
	<CompilerInfo packageName="adapter::types::unidirectional">
	</CompilerInfo>
	<InterfaceList>
		<EventOutputs>
			<Event Name="SET" Type="Event" Comment="Set / Switch on">
			</Event>
			<Event Name="RESET" Type="Event" Comment="Reset / Switch off">
			</Event>
			<Event Name="TOGGLE" Type="Event" Comment="Toggle / Switch output">
			</Event>
		</EventOutputs>
	</InterfaceList>
	<Attribute Name="eclipse4diac::core::TypeHash" Value="''"/>
</AdapterType>
