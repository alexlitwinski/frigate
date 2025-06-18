# Frigate Camera Control

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)

Integração personalizada para Home Assistant que permite habilitar e desabilitar câmeras do Frigate em tempo real sem modificar o arquivo de configuração.

## Características

- 🎯 **Controle em tempo real**: Habilite/desabilite câmeras sem reiniciar o Frigate
- 🔄 **Sincronização automática**: Detecta automaticamente todas as câmeras configuradas
- 🎛️ **Interface intuitiva**: Switches no Home Assistant para cada câmera
- 📡 **API REST**: Utiliza a API nativa do Frigate
- ⚡ **Performance**: Polling otimizado com coordinator

## Instalação via HACS

### 1. Adicionar Repositório Personalizado

1. Abra o HACS no Home Assistant
2. Clique nos três pontos no canto superior direito
3. Selecione "Custom repositories"
4. Adicione a URL: `https://github.com/[SEU_USUARIO]/frigate-camera-control`
5. Categoria: "Integration"
6. Clique em "ADD"

### 2. Instalar a Integração

1. No HACS, vá para "Integrations"
2. Procure por "Frigate Camera Control"
3. Clique em "INSTALL"
4. Reinicie o Home Assistant

## Configuração

### 1. Adicionar a Integração

1. Vá para **Configurações** → **Dispositivos e Serviços**
2. Clique em **"+ ADICIONAR INTEGRAÇÃO"**
3. Procure por **"Frigate Camera Control"**
4. Insira as informações do seu servidor Frigate:
   - **Host**: IP ou hostname do Frigate (ex: `192.168.1.100`)
   - **Porta**: Porta do Frigate (padrão: `5000`)

### 2. Verificar Entidades

Após a configuração, você verá switches para cada câmera:
- `switch.frigate_camera_entrada`
- `switch.frigate_camera_garagem`
- etc.

## Uso

### No Home Assistant

1. **Painel**: Adicione os switches ao seu painel
2. **Automações**: Use os switches em automações
3. **Scripts**: Controle via scripts

### Exemplo de Automação

```yaml
alias: "Desabilitar câmeras durante o dia"
trigger:
  - platform: time
    at: "08:00:00"
action:
  - service: switch.turn_off
    target:
      entity_id:
        - switch.frigate_camera_entrada
        - switch.frigate_camera_garagem
```

### Exemplo de Script

```yaml
alias: "Modo Noturno"
sequence:
  - service: switch.turn_on
    target:
      entity_id: switch.frigate_camera_entrada
  - service: switch.turn_on
    target:
      entity_id: switch.frigate_camera_garagem
```

## Requisitos

- Home Assistant 2023.1.0 ou superior
- Frigate NVR em execução
- Acesso à API REST do Frigate (porta 5000 por padrão)

## API do Frigate

Esta integração utiliza os seguintes endpoints da API do Frigate:

- `GET /api/config` - Obter configuração e status das câmeras
- `PUT /api/{camera_name}/enable` - Habilitar câmera
- `PUT /api/{camera_name}/disable` - Desabilitar câmera

## Problemas Conhecidos

- As câmeras podem levar alguns segundos para responder após a mudança de estado
- Verifique se a API do Frigate está acessível na rede

## Contribuindo

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## Licença

Distribuído sob a licença MIT. Veja `LICENSE` para mais informações.

## Suporte

Se você encontrar problemas ou tiver sugestões:
- Abra uma [issue](https://github.com/[SEU_USUARIO]/frigate-camera-control/issues)
- Contribua com melhorias via Pull Request
