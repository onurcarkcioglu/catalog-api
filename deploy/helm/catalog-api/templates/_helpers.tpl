{{- define "catalog.selector" -}}
app.kubernetes.io/name: {{ .Chart.Name }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}
{{- define "catalog.labels" -}}
{{ include "catalog.selector" . }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
app.kubernetes.io/part-of: securestream
{{- end }}
{{- define "catalog.image" -}}
{{- if .Values.image.digest -}}
{{ .Values.image.repository }}@{{ .Values.image.digest }}
{{- else -}}
{{ .Values.image.repository }}:{{ .Values.image.tag }}
{{- end -}}
{{- end }}
