<?xml version="1.0" encoding="UTF-8"?>
<AdapterType Name="AFIFO_UINT" Comment="Adapter fuer FIFO_UINT (FIFO_adapter): Konsument haengt per Socket an - DATA&#10;liefert PLUG-&gt;SOCKET den naechsten Wert, PROCESSED quittiert SOCKET-&gt;PLUG&#10;dessen Verarbeitung. Kein eigener Event-Baustein auf Konsumentenseite noetig -&#10;der Rueckkanal des Adapters selbst traegt die Quittung.">
	<Identification Standard="61499-1" Description="Copyright (c) 2026 Meisterschulen am Ostbahnhof&#10; &#10;This program and the accompanying materials are made&#10;available under the terms of the Eclipse Public License 2.0&#10;which is available at https://www.eclipse.org/legal/epl-2.0/&#10;&#10;SPDX-License-Identifier: EPL-2.0">
	</Identification>
	<VersionInfo Organization="Meisterschulen am Ostbahnhof" Version="1.1" Author="Franz Höpfinger" Date="2026-11-08" Remarks="N (Fuellstand der Queue) wird mit DATA mitgeliefert.">
	</VersionInfo>
	<VersionInfo Organization="Meisterschulen am Ostbahnhof" Version="1.0" Author="Franz Höpfinger" Date="2026-10-13" Remarks="initial API and implementation and/or initial documentation">
	</VersionInfo>
	<CompilerInfo packageName="FIFO_adapter">
	</CompilerInfo>
	<InterfaceList>
		<EventInputs>
			<Event Name="PROCESSED" Type="Event" Comment="Konsument (SOCKET) bestaetigt: OUT ist verarbeitet, der naechste Wert (falls vorhanden) kann geliefert werden">
			</Event>
		</EventInputs>
		<EventOutputs>
			<Event Name="DATA" Type="Event" Comment="PLUG (FIFO) liefert einen neuen Wert - es folgt kein weiteres DATA, bevor nicht PROCESSED eingetroffen ist">
				<With Var="OUT"/>
				<With Var="N"/>
			</Event>
		</EventOutputs>
		<OutputVars>
			<VarDeclaration Name="OUT" Type="UINT" Comment="Gelieferter Wert, gueltig bis zur naechsten PROCESSED-Bestaetigung"/>
			<VarDeclaration Name="N" Type="UINT" Comment="Anzahl der danach noch wartenden Elemente in der Queue"/>
		</OutputVars>
	</InterfaceList>
	<Attribute Name="eclipse4diac::core::TypeHash" Value="''"/>
</AdapterType>
