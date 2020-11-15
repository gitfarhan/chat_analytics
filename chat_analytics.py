import pandas as pd
import matplotlib.pyplot as plt
import click

class ChatParsing:

    __is_ios = False

    def __init__(self, chat_path, exported_filename='clean_chat.csv'):
        self.chat_path = chat_path
        self.exported_filename = exported_filename
        with open(self.chat_path, 'r', encoding='utf-8') as h:
            self.__history = h.read()

    def __to_pandas(self):
        self.__is_ios = self.__history[0] == '['
        def startsWithDate(s):

            if self.__is_ios:
                if s[0] == '[':
                    return '~StartsWithDate~'
                else:
                    return ''
            else:
                is_digit = str(s[0]).isdigit()
                datefmt = str(s).split(',')[0]
                if is_digit and '/' in datefmt:

                    return '~StartsWithDate~'
                else:
                    return ' '

        s = '\n'.join(['\n' if i == '' else f"{startsWithDate(i)} {i}".strip() for i in self.__history.split('\n')]).split(
            "~StartsWithDate~ ")

        s = [i.strip('\n') for i in s]

        chat_dict = []
        for i in s:

            # ios
            if self.__is_ios:
                date = i[1:9].strip()
                time = i[9:15].strip()
                chat = i[16:]

                coord = chat.find(':')
                if coord > 0:
                    sender = chat[4:coord].strip()
                    text = chat[(coord + 1):].strip()
                    chat_dict.append(dict(
                        date=date,
                        time=time,
                        sender=sender,
                        text=text
                    ))
            else:
                date = i.split(',')[0]
                time = i[9:15].strip()
                chat = i[16:]
                coord = chat.find(':')
                if coord > 0:
                    sender = chat[1:coord].strip()
                    text = chat[(coord + 1):].strip()
                    chat_item = dict(
                        date=date,
                        time=time,
                        sender=sender,
                        text=text
                    )
                    chat_dict.append(chat_item)

        chat_df = pd.DataFrame(chat_dict)

        return chat_df

    def run(self):
        chat_df = self.__to_pandas()

        chat_df['?'] = chat_df['text'].str.contains("""[?]""").astype(int)
        qmarks_counter = chat_df.groupby(['date', 'sender'])['?'].sum()\
            .reset_index()\
            .rename(columns={'?': 'total'})

        qmarks_counter = qmarks_counter[qmarks_counter.date.str.split('/').str.len() >= 3]

        if self.__is_ios:
            qmarks_counter.date = pd.to_datetime(qmarks_counter.date, format="%d/%m/%y")
        else:
            qmarks_counter.date = pd.to_datetime(qmarks_counter.date, format="%d/%m/%Y")

        qmarks_counter = qmarks_counter.sort_values(by='date')


        # visualize
        plt.figure("Chat Analytics")
        df = qmarks_counter.pivot(index='date', columns='sender', values='total')
        df = df.fillna(0)

        df.iloc[:,0].plot(grid=True, label=df.iloc[:,0].name, legend=True)
        df.iloc[:,1].plot(grid=True, label=df.iloc[:,1].name, legend=True)

        plt.title('? counter')
        plt.ylabel('? count')
        plt.show()

@click.command()
@click.option('--filepath', '-f')
def main(filepath):
    chat = ChatParsing(chat_path=filepath)
    chat.run()

if __name__ == '__main__':
    main()