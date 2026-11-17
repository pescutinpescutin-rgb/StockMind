"""Financial education text for StockMind."""

EXPLANATIONS = {
    "Revenue": (
        "Revenue is the gross income from ordinary business activities before expenses, taxes, or financing costs.",
        "Revenue is the money a company brings in from selling its products or services, before paying its bills.",
    ),
    "Net income": (
        "Net income is profit after operating costs, interest, taxes, and other expenses for the reporting period.",
        "Net income is what remains after the company has paid its expenses and taxes.",
    ),
    "Profit margin": (
        "Net profit margin is net income divided by revenue; it measures the share of sales retained as profit.",
        "It shows how much profit the company keeps from each euro or dollar of sales.",
    ),
    "Debt": (
        "Debt represents contractual borrowing obligations. Assess maturity, interest costs, cash flows, and liquidity alongside the balance.",
        "Debt is money the company owes. Whether it is manageable depends on its cash and ability to make payments.",
    ),
    "P/E ratio": (
        "Price-to-earnings is share price divided by earnings per share, usually trailing or forward. It is not meaningful for negative earnings.",
        "P/E compares the share price with the company's earnings per share. A higher number does not by itself mean a share is expensive.",
    ),
}

GERMAN = {
    "Revenue": (
        "Der Umsatz umfasst die Erlöse aus der gewöhnlichen Geschäftstätigkeit vor Kosten, Steuern und Finanzierung.",
        "Der Umsatz ist das Geld, das ein Unternehmen durch Verkäufe einnimmt, bevor es Rechnungen bezahlt.",
    ),
    "Net income": (
        "Der Jahresüberschuss ist der Gewinn nach Betriebsaufwand, Zinsen, Steuern und sonstigen Aufwendungen.",
        "Der Jahresüberschuss ist das, was nach Kosten und Steuern übrig bleibt.",
    ),
    "Profit margin": (
        "Die Nettomarge ist der Jahresüberschuss geteilt durch den Umsatz und misst den Gewinnanteil am Umsatz.",
        "Sie zeigt, wie viel Gewinn das Unternehmen von einem Euro Umsatz behält.",
    ),
    "Debt": (
        "Die Verschuldung umfasst vertragliche Kreditverpflichtungen. Laufzeiten, Zinskosten, Cashflows und Liquidität gehören zur Beurteilung.",
        "Schulden sind Geld, das das Unternehmen zurückzahlen muss. Entscheidend ist auch, ob genug Geld dafür vorhanden ist.",
    ),
    "P/E ratio": (
        "Das Kurs-Gewinn-Verhältnis setzt Aktienkurs ins Verhältnis zum Gewinn je Aktie. Bei negativem Gewinn ist es nicht aussagekräftig.",
        "Das KGV vergleicht den Aktienkurs mit dem Gewinn je Aktie. Ein hoher Wert bedeutet allein nicht, dass eine Aktie teuer ist.",
    ),
}

SPANISH = {
    "Revenue": (
        "Los ingresos son el beneficio bruto de la actividad empresarial ordinaria antes de gastos, impuestos y costes financieros.",
        "Los ingresos son el dinero que una empresa obtiene por vender sus productos o servicios, antes de pagar sus gastos.",
    ),
    "Net income": (
        "El beneficio neto es el resultado tras gastos operativos, intereses, impuestos y otros costes del periodo.",
        "El beneficio neto es lo que queda después de que la empresa haya pagado sus costes e impuestos.",
    ),
    "Profit margin": (
        "El margen de beneficio neto es el beneficio neto dividido entre los ingresos; mide la parte de las ventas que queda como beneficio.",
        "Muestra cuánto beneficio conserva la empresa por cada euro o dólar de ventas.",
    ),
    "Debt": (
        "La deuda representa obligaciones de endeudamiento contractuales. Hay que valorar vencimientos, costes de financiación, flujo de caja y liquidez.",
        "La deuda es dinero que la empresa debe. Si es manejable depende de su efectivo y de su capacidad para pagar.",
    ),
    "P/E ratio": (
        "La relación precio-beneficio compara el precio de la acción con el beneficio por acción. No tiene sentido cuando el beneficio es negativo.",
        "El ratio P/E compara el precio de la acción con el beneficio por acción. Un valor más alto no significa por sí solo que la acción sea cara.",
    ),
}

ITALIAN = {
    "Revenue": (
        "Il fatturato è il ricavo lordo derivante dall'attività ordinaria prima di costi, tasse e oneri finanziari.",
        "Il fatturato è il denaro che l'azienda riceve dalla vendita dei propri prodotti o servizi, prima di pagare le spese.",
    ),
    "Net income": (
        "L'utile netto è il profitto dopo costi operativi, interessi, tasse e altri oneri del periodo.",
        "L'utile netto è ciò che resta dopo che l'azienda ha pagato le spese e le tasse.",
    ),
    "Profit margin": (
        "Il margine di utile netto è l'utile netto diviso per il fatturato; misura la quota delle vendite che resta come profitto.",
        "Mostra quanto profitto l'azienda trattiene da ogni euro o dollaro di vendite.",
    ),
    "Debt": (
        "Il debito rappresenta obbligazioni di finanziamento contrattuali. Nella valutazione vanno considerati scadenze, costi finanziari, flussi di cassa e liquidità.",
        "Il debito è denaro che l'azienda deve. Se è sostenibile dipende da quanto contante ha e dalla sua capacità di pagare.",
    ),
    "P/E ratio": (
        "Il rapporto prezzo/utili confronta il prezzo dell'azione con l'utile per azione; non è significativo quando l'utile è negativo.",
        "Il P/E confronta il prezzo dell'azione con l'utile per azione. Un valore più alto non significa automaticamente che un'azione sia costosa.",
    ),
}

CHINESE = {
    "Revenue": (
        "收入是公司正常经营活动产生的总收入，通常在扣除成本、税费和融资成本之前。",
        "收入是公司通过销售产品或服务获得的现金，在支付各项开支之前。",
    ),
    "Net income": (
        "净利润是公司在扣除运营成本、利息、税费和其他费用后的利润。",
        "净利润是公司支付所有费用和税后剩余的金额。",
    ),
    "Profit margin": (
        "净利润率是净利润除以收入，衡量公司从销售中保留多少利润。",
        "它显示公司每一美元或每一欧元销售额中保留了多少利润。",
    ),
    "Debt": (
        "债务代表合同约定的借款责任，需要综合看到期时间、利息成本、现金流和流动性。",
        "债务是公司欠下的钱。它是否可控，取决于现金和偿还能力。",
    ),
    "P/E ratio": (
        "市盈率是股票价格与每股收益的比值；当收益为负时，这个指标通常没有意义。",
        "市盈率比较了股价和每股收益。较高的数值不一定说明股票一定贵。",
    ),
}

JAPANESE = {
    "Revenue": (
        "売上高は、費用・税金・金融費用を差し引く前の通常事業による収益の総額です。",
        "売上高は、製品やサービスの販売によって会社が得たお金で、支出を支払う前の額です。",
    ),
    "Net income": (
        "純利益は、営業費用・利息・税金・その他の費用を差し引いた後の利益です。",
        "純利益は、会社が費用や税金を支払った後に残る金額です。",
    ),
    "Profit margin": (
        "純利益率は純利益を売上高で割ったもので、売上のうちどれだけが利益になるかを示します。",
        "会社が1ドルや1ユーロの売上からどれだけ利益を残せるかを示します。",
    ),
    "Debt": (
        "負債は契約上の借入義務であり、返済期限、金利、キャッシュフロー、流動性を併せて見る必要があります。",
        "負債は会社が返済しなければならないお金です。管理可能かどうかは現金と支払能力で判断します。",
    ),
    "P/E ratio": (
        "PERは株価を1株当たり利益で割ったもので、収益がマイナスなら意味が薄れます。",
        "PERは株価と1株当たり利益の比較です。高いからといって必ず割高とは限りません。",
    ),
}

KOREAN = {
    "Revenue": (
        "매출은 운영 비용, 세금, 금융 비용을 차감하기 전의 일반 사업 활동에서 발생한 총 수익입니다.",
        "매출은 제품이나 서비스를 판매해 회사가 벌어들인 돈으로, 비용을 지불하기 전의 금액입니다.",
    ),
    "Net income": (
        "순이익은 영업 비용, 이자, 세금 및 기타 비용을 차감한 후의 이익입니다.",
        "순이익은 회사가 비용과 세금을 지불한 뒤 남는 금액입니다.",
    ),
    "Profit margin": (
        "순이익률은 순이익을 매출로 나눈 값으로, 판매 수익 중 얼마나 이익으로 남는지를 보여줍니다.",
        "회사가 매출 1달러 또는 1유로에서 얼마나 이익을 남기는지를 보여줍니다.",
    ),
    "Debt": (
        "부채는 계약상 차입 의무이며, 만기, 이자 비용, 현금 흐름, 유동성을 함께 봐야 합니다.",
        "부채는 회사가 갚아야 하는 돈입니다. 부담 가능 여부는 현금과 상환 능력에 달려 있습니다.",
    ),
    "P/E ratio": (
        "PER은 주가를 주당순이익으로 나눈 값이며, 이익이 마이너스면 의미가 약해집니다.",
        "PER은 주가와 주당순이익을 비교합니다. 높다고 해서 무조건 비싸다고 볼 수는 없습니다.",
    ),
}

HINDI = {
    "Revenue": (
        "रेल्स एक सामान्य व्यावसायिक गतिविधि से अर्जित सकल आय है, खर्च, कर और वित्तीय लागत से पहले।",
        "रेवेन्यू वह पैसा है जो कंपनी अपने उत्पाद या सेवाएँ बेचकर कमाती है, खर्च चुकाने से पहले।",
    ),
    "Net income": (
        "शुद्ध लाभ वह लाभ है जो परिचालन लागत, ब्याज, कर और अन्य खर्चों के बाद बचता है।",
        "शुद्ध लाभ वह पैसा है जो कंपनी अपने सभी खर्च और करों के बाद बचाती है।",
    ),
    "Profit margin": (
        "शुद्ध लाभ मार्जिन शुद्ध लाभ को राजस्व से विभाजित करने से आता है, जो बिक्री का कितना हिस्सा लाभ में रहता है दिखाता है।",
        "यह बताता है कि कंपनी बिक्री के हर डॉलर या रुपए में से कितना लाभ बनाकर रखती है।",
    ),
    "Debt": (
        "ऋण अनुबंधित उधारी दायित्व है। परिपक्वता, ब्याज लागत, नकदी प्रवाह और तरलता को भी देखा जाना चाहिए।",
        "ऋण वह पैसा है जो कंपनी को लौटाना पड़ता है। यह संभालने योग्य है या नहीं, इसकी नकद स्थिति और चुकौती क्षमता पर निर्भर करता है।",
    ),
    "P/E ratio": (
        "P/E अनुपात स्टॉक कीमत को प्रति शेयर कमाई से विभाजित करता है; कमाई नकारात्मक होने पर यह उपयोगी नहीं होता है।",
        "P/E स्टॉक कीमत और प्रति शेयर कमाई की तुलना करता है। उच्च मान का मतलब हमेशा ज्यादा महंगा होना नहीं है।",
    ),
}


def metric_explanation(name, language="English"):
    if language == "Deutsch":
        explanations = GERMAN
    elif language == "Español":
        explanations = SPANISH
    elif language == "Italiano":
        explanations = ITALIAN
    elif language == "中文":
        explanations = CHINESE
    elif language == "日本語":
        explanations = JAPANESE
    elif language == "한국어":
        explanations = KOREAN
    elif language == "हिन्दी":
        explanations = HINDI
    else:
        explanations = EXPLANATIONS
    return explanations[name]
