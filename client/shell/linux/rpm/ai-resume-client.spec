Name:           ai-resume-client
Version:        1.0.0
Release:        1%{?dist}
Summary:        AI 简历生成器桌面客户端(C/S)
License:        Proprietary
URL:            https://example.invalid/local
# 依赖名称按发行版调整:Fedora 为 python3-qt6-base / python3-qt6-webengine(或 PyQt6 系),
# openSUSE 为 python3-Qt6 相关;构建前请用 `dnf repoquery` 校正。
BuildArch:      x86_64
Requires:       python3
Requires:       python3-qt6-webengine

%description
AI 简历生成器的 Linux 桌面客户端,连接服务端完成注册/登录、
简历 AI 生成、知识库与 Word/PDF 导出。需要配合 ai-resume-server 使用。

%prep
# 无源码解压;载荷由 build_client_linux.sh 预先放到 ~/rpmbuild/SOURCES/

%build

%install
mkdir -p %{buildroot}/opt/ai-resume-client %{buildroot}%{_bindir} %{buildroot}%{_datadir}/applications
cp -r %{_sourcedir}/payload/opt/ai-resume-client/. %{buildroot}/opt/ai-resume-client/
cat > %{buildroot}%{_bindir}/ai-resume-client <<'EOF'
#!/bin/sh
exec python3 /opt/ai-resume-client/ai_resume_client.py "$@"
EOF
chmod 755 %{buildroot}%{_bindir}/ai-resume-client
cp %{_sourcedir}/payload/ai-resume-client.desktop %{buildroot}%{_datadir}/applications/

%files
/opt/ai-resume-client
%{_bindir}/ai-resume-client
%{_datadir}/applications/ai-resume-client.desktop
