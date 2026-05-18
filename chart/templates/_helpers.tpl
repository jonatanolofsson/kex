{{- define "kex.name" -}}
kex
{{- end -}}

{{- define "kex.labels" -}}
app.kubernetes.io/name: {{ include "kex.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end -}}

{{- define "kex.selectorLabels" -}}
app.kubernetes.io/name: {{ include "kex.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end -}}
