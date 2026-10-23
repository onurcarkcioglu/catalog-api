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
{{- $digest := required "image.digest zorunlu (sha256:...); imaj yalnizca digest ile deploy edilir" .Values.image.digest -}}
{{- if not (regexMatch "^sha256:[a-f0-9]{64}$" $digest) -}}
{{- fail (printf "image.digest gecersiz: %q" $digest) -}}
{{- end -}}
{{ .Values.image.repository }}@{{ $digest }}
{{- end }}
