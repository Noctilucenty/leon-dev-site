"""Visible, illustrative workflows. No simulated event is a real submission."""
from html import escape

SERVICE_FLOWS = {
    'websites': ('Show what you do. Make the next step obvious.', ['Visitor', 'Clear offer', 'Inquiry']),
    'mobile-apps': ('Start with the smallest useful app.', ['App idea', 'Usable version', 'Store submission']),
    'ai-chatbots': ('Routine questions answered. Your team handles the exceptions.', ['Question', 'Approved information', 'Answer or handoff']),
    'ai-phone-agents': ('A clear next step for incoming calls.', ['Incoming call', 'Agreed rules', 'Answer or transfer']),
    'business-automation': ('Stop moving the same details by hand.', ['Form arrives', 'Tools connect', 'Agreed follow-up']),
    'custom-software': ('One workspace for the way your team works.', ['Your process', 'Shared records', 'Team workspace']),
    'booking-systems': ('Let customers choose a time and know what happens next.', ['Choose a time', 'Calendar entry', 'Reminder']),
    'business-dashboards': ('Your existing data. One useful view.', ['Existing data', 'One screen', 'Daily review']),
    'seo': ('Help people find and understand your pages.', ['Site audit', 'Clear pages', 'Measure changes']),
}
INDUSTRY_FLOWS = {
    'restaurants': ('From a readable menu to a clear ordering path.', ['Phone-friendly menu', 'Direct cart', 'Order ticket']),
    'contractors': ('Keep estimate requests moving while you work.', ['Quote request', 'Owner notified', 'Follow-up']),
    'automotive': ('Keep customers informed without another manual update.', ['Shop system', 'Job completed', 'Customer update']),
    'healthcare': ('Make the administrative side of a visit simpler.', ['Choose a visit', 'Appointment', 'Reminder']),
    'real-estate': ('Keep a maintenance request and its next step together.', ['Tenant request', 'Vendor handoff', 'Status update']),
    'logistics': ('Connect dispatch, drivers and customer updates.', ['Load assigned', 'Driver update', 'Customer tracking']),
    'gyms': ('A simpler path from choosing a class to showing up.', ['Choose a class', 'Booking', 'Class reminder']),
    'retail': ('Bring incoming orders into one place.', ['Orders arrive', 'One queue', 'Staff alert']),
    'professional-services': ('Give each client request a clear next step.', ['Client intake', 'Document workflow', 'Client portal']),
    'startups': ('Build something people can try before making it bigger.', ['Product idea', 'Small release', 'Users try it']),
}
FLOW_CAUTIONS = {
    'mobile-apps': 'Store submission support does not guarantee approval.',
    'ai-chatbots': 'AI can make mistakes. Sensitive decisions stay with people.',
    'ai-phone-agents': 'AI can make mistakes. Unusual requests need a human handoff.',
    'seo': 'Search rankings are not guaranteed.',
    'healthcare': 'Administrative support, not medical advice or a compliance guarantee.',
    'restaurants': 'Integrations are checked before quoting. The diagram is not a live order.',
    'retail': 'Integrations are checked before quoting. The diagram is not a live order.',
}


def flow_scene(labels, key='workflow', language='en'):
    text = {
        'en': ('Example workflow', 'Play example', 'Illustration only. Nothing is sent.', 'Example complete'),
        'es': ('Ejemplo de proceso', 'Ver ejemplo', 'Solo una ilustración. No se envía nada.', 'Ejemplo terminado'),
        'pt': ('Exemplo de processo', 'Ver exemplo', 'Apenas uma ilustração. Nada é enviado.', 'Exemplo concluído'),
        'zh': ('流程示意', '播放示例', '仅为示意，不会发送任何信息。', '示例完成'),
    }[language]
    # Decorative interface fragments explain each object; the stage label is text.
    fragments = {
        'website': ['<span class="mini-page"><i></i><i></i><i></i></span>', '<span class="mini-gallery"><i></i><i></i><i></i></span>', '<span class="mini-contact"><i></i><i></i><b>↗</b></span>'],
        'automation': ['<span class="mini-form"><i></i><i></i><b>↗</b></span>', '<span class="mini-inbox"><i></i><i></i><i></i></span>', '<span class="mini-message"><i></i><i></i></span>'],
        'custom': ['<span class="mini-form"><i></i><i></i><b>↗</b></span>', '<span class="mini-rule"><i></i><b>?</b><i></i></span>', '<span class="mini-person"><i></i><b>✓</b></span>'],
    }.get(key, ['<span class="flow-mini-lines"><i></i><i></i></span>'] * 3)
    nodes = ''.join(
        f'<div class="flow-node flow-node-{index}"><span class="flow-window-bar" aria-hidden="true"><i></i><i></i><i></i></span>'
        f'<div class="flow-node-face"><span class="flow-node-symbol" aria-hidden="true">{symbol}</span><strong>{escape(label)}</strong>'
        f'<span class="flow-object" aria-hidden="true">{fragments[index]}</span></div></div>'
        + ('<span class="flow-connector" aria-hidden="true"><i></i><b>→</b></span>' if index < 2 else '')
        for index, (label, symbol) in enumerate(zip(labels, ['↗', '⌘', '✓']))
    )
    return f'''<div class="flow-scene" data-flow="{escape(key)}">
<div class="flow-scene-top"><span>{text[0]}</span><button type="button" class="flow-play" data-flow-play hidden>{text[1]} <span aria-hidden="true">↻</span></button></div>
<div class="flow-stage">{nodes}</div>
<div class="flow-scene-bottom"><small>{text[2]}</small><span class="flow-feedback" aria-live="polite" data-complete="{text[3]}"></span></div>
</div>'''


def service_visual(slug):
    summary, labels = SERVICE_FLOWS[slug]
    caution = FLOW_CAUTIONS.get(slug, 'Final scope, integrations and provider fees are confirmed before the build.')
    return f'<p class="visual-intro">{escape(summary)}</p>{flow_scene(labels, slug)}<p class="visual-caution">{escape(caution)}</p>'


def industry_visual(slug):
    summary, labels = INDUSTRY_FLOWS[slug]
    caution = FLOW_CAUTIONS.get(slug, 'An example of the process—not a promise of business results. Integrations are checked first.')
    return f'<p class="visual-intro">{escape(summary)}</p>{flow_scene(labels, slug)}<p class="visual-caution">{escape(caution)}</p>'


LOCAL_FLOWS = {
    'es': {
        'websites': ('Muestra lo que haces. Facilita el contacto.', ['Visita', 'Servicios', 'Contacto']),
        'automation': ('Deja de copiar los mismos datos a mano.', ['Formulario', 'Herramientas', 'Seguimiento']),
        'ordering': ('Del menú al pedido, con un siguiente paso claro.', ['Menú', 'Carrito', 'Pedido']),
        'caution': 'Las conexiones, el alcance y las tarifas de proveedores se revisan antes de presupuestar.',
        'details': 'Ver alcance, ejemplos y detalles',
    },
    'pt': {
        'websites': ('Mostre o que você faz. Facilite o contato.', ['Visita', 'Serviços', 'Contato']),
        'automation': ('Pare de copiar os mesmos dados à mão.', ['Formulário', 'Ferramentas', 'Retorno']),
        'ordering': ('Do cardápio ao pedido, com um próximo passo claro.', ['Cardápio', 'Carrinho', 'Pedido']),
        'caution': 'Conexões, escopo e taxas dos fornecedores são verificados antes do orçamento.',
        'details': 'Ver escopo, exemplos e detalhes',
    },
    'zh': {
        'websites': ('让客户看懂你的服务，轻松联系你。', ['访客', '服务介绍', '联系']),
        'automation': ('不用再手动重复复制相同的信息。', ['收到表单', '连接工具', '后续跟进']),
        'ordering': ('从菜单到下单，每一步都清楚。', ['菜单', '购物车', '订单']),
        'caution': '报价前会确认系统能否连接、项目范围和第三方费用。',
        'details': '查看项目范围、示例和详细说明',
    },
}


def local_visual(lang, key):
    content = LOCAL_FLOWS[lang]
    summary, labels = content[key]
    return f'<p class="visual-intro">{escape(summary)}</p>{flow_scene(labels, key, lang)}<p class="visual-caution">{escape(content["caution"])}</p>'


def choice_scene():
    options = [
        ('website', 'Website', 'Show my business', 'Help customers understand your services and contact, book or buy through standard pages and tools.',
         'Check editing access, recurring fees and whether you can export your content.', ['Services', 'Work', 'Contact']),
        ('automation', 'Automation', 'Connect my tools', 'Pass requests to the right place and person without copying details by hand.',
         'Decide who handles failed connections and unanswered requests.', ['Form', 'Inbox', 'Reply']),
        ('custom', 'Custom software', 'Run my own process', 'Build a small tool when existing tools cannot handle an important rule, permission or approval.',
         'Plan for maintenance, backups and handover—not just the first build.', ['Request', 'Rule check', 'Human approval']),
    ]
    controls = ''.join(f'<label class="build-choice"><input type="radio" name="build-choice" value="{key}" {"checked" if n == 0 else ""}><span><small>{name}</small><strong>{label}</strong></span></label>'
                       for n, (key, name, label, _, _, _) in enumerate(options))
    panels = ''.join(f'<section class="choice-panel" data-choice-panel="{key}" aria-label="{name}">'
                     f'{flow_scene(labels, key)}<div class="choice-explanation"><h2>{name}</h2><p>{summary}</p></div><p class="visual-caution">{caution}</p></section>'
                     for key, name, _, summary, caution, labels in options)
    return f'''<div class="visual-chooser"><fieldset class="build-choices"><legend>What needs to work better?</legend>{controls}</fieldset>{panels}</div>'''
