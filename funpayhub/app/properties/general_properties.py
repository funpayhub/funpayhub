from __future__ import annotations

__all__ = ['GeneralProperties',]


from funpayhub.lib.properties import Properties, ChoiceParameter
from funpayhub.lib.properties.parameter.choice_parameter import Item


class GeneralProperties(Properties):
    def __init__(self) -> None:
        super().__init__(
            id='general',
            name='$props.general:name',
            description='$props.general:description'
        )

        self.language = self.attach_parameter(
            ChoiceParameter(
                properties=self,
                id='language',
                name='$props.general.language:name',
                description='$props.general.language:description',
                choices=(
                    Item('🇷🇺 Русский', 'ru'),
                    Item('🇬🇧 English', 'en'),
                    Item('🇺🇦 Українська', 'uk'),
                    Item('🍌 Bacunana', 'banana'),
                    Item('🇪🇸 Español', 'es'),
                    Item('🇫🇷 Français', 'fr'),
                    Item('🇩🇪 Deutsch', 'de'),
                    Item('🇮🇹 Italiano', 'it'),
                    Item('🇵🇹 Português', 'pt'),
                    Item('🇳🇱 Nederlands', 'nl'),
                    Item('🇸🇪 Svenska', 'sv'),
                    Item('🇳🇴 Norsk', 'no'),
                    Item('🇩🇰 Dansk', 'da'),
                    Item('🇫🇮 Suomi', 'fi'),
                    Item('🇵🇱 Polski', 'pl'),
                    Item('🇨🇿 Čeština', 'cs'),
                    Item('🇸🇰 Slovenčina', 'sk'),
                    Item('🇭🇺 Magyar', 'hu'),
                    Item('🇷🇴 Română', 'ro'),
                    Item('🇧🇬 Български', 'bg'),
                    Item('🇬🇷 Ελληνικά', 'el'),
                    Item('🇹🇷 Türkçe', 'tr'),
                    Item('🇸🇦 العربية', 'ar'),
                    Item('🇮🇱 עברית', 'he'),
                    Item('🇮🇳 हिन्दी', 'hi'),
                    Item('🇧🇩 বাংলা', 'bn'),
                    Item('🇵🇰 اردو', 'ur'),
                    Item('🇮🇷 فارسی', 'fa'),
                    Item('🇨🇳 中文', 'zh'),
                    Item('🇯🇵 日本語', 'ja'),
                    Item('🇰🇷 한국어', 'ko'),
                    Item('🇹🇭 ไทย', 'th'),
                    Item('🇻🇳 Tiếng Việt', 'vi'),
                    Item('🇮🇩 Bahasa Indonesia', 'id'),
                    Item('🇲🇾 Bahasa Melayu', 'ms'),
                    Item('🇰🇪 Kiswahili', 'sw'),
                    Item('🇿🇦 IsiZulu', 'zu'),
                    Item('🇿🇦 isiXhosa', 'xh'),
                    Item('🌐 አማርኛ', 'am'),
                    Item('🇸🇴 Soomaali', 'so'),
                    Item('🇳🇵 नेपाली', 'ne'),
                    Item('🇱🇰 සිංහල', 'si'),
                    Item('🇮🇳 தமிழ்', 'ta'),
                    Item('🇮🇳 తెలుగు', 'te'),
                    Item('🇮🇳 ಕನ್ನಡ', 'kn'),
                    Item('🇮🇳 മലയാളം', 'ml'),
                    Item('🇮🇳 मराठी', 'mr'),
                    Item('🇮🇳 ગુજરાતી', 'gu'),
                    Item('🇮🇳 ਪੰਜਾਬੀ', 'pa'),
                    Item('🇳🇬 Igbo', 'ig'),
                    Item('🇳🇬 Yorùbá', 'yo'),
                    Item('🇳🇬 Hausa', 'ha'),
                    Item('🇵🇭 Filipino', 'tl'),
                    Item('🇮🇩 Jawa', 'jv'),
                ),
                default_value=0,
            )
        )
