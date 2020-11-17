import pandas as pd
import matplotlib.pyplot as plt
import click
from text_mining import TextCleaner

class ChatAnalytics:

    __is_ios = False

    def __init__(self, chat_path):
        self.chat_path = chat_path
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
        chat_df = chat_df[~chat_df.text.str.contains('are end-to-end')]
        senders = list(chat_df.sender.unique())
        sender_1 = senders[0]
        sender_2 = senders[1]
        
        sender_1_df = chat_df[chat_df.sender == sender_1]
        sender_2_df = chat_df[chat_df.sender == sender_2]
        
        sender_1_text = " ".join(list(sender_1_df.text))
        sender_2_text = " ".join(list(sender_2_df.text))
        

        cleaner = TextCleaner()
        
        sender_1_wordcount_df = cleaner.get_clean_text(text=sender_1_text)
        sender_1_wordcount_df = sender_1_wordcount_df[sender_1_wordcount_df.word != 'omitted']
        sender_1_wordcount_df = sender_1_wordcount_df[sender_1_wordcount_df['count'] > 2]
        sender_1_wordcount_df = sender_1_wordcount_df.head(20)
        
        
        sender_2_wordcount_df = cleaner.get_clean_text(text=sender_2_text)
        sender_2_wordcount_df = sender_2_wordcount_df[sender_2_wordcount_df.word != 'omitted']
        sender_2_wordcount_df = sender_2_wordcount_df[sender_2_wordcount_df['count'] > 2]
        sender_2_wordcount_df = sender_2_wordcount_df.head(20)
        

        chat_df['?'] = chat_df['text'].str.contains("""[?]""").astype(int)
        qmarks_counter = chat_df.groupby(['date', 'sender'])['?'].sum()\
            .reset_index()\
            .rename(columns={'?': 'total'})

        qmarks_counter = qmarks_counter[qmarks_counter.date.str.split('/').str.len() >= 3]

        try:
            if self.__is_ios:
                qmarks_counter.date = pd.to_datetime(qmarks_counter.date, format="%d/%m/%y")
            else:
                qmarks_counter.date = pd.to_datetime(qmarks_counter.date, format="%d/%m/%Y")
        except Exception as e:
            print(f"faield to covert to datetime format: {e}")

        qmarks_counter = qmarks_counter.sort_values(by='date')


        # visualize
        
        
        # plot size
        # plt.rcParams["figure.figsize"] = (15, 5)

        fig = plt.figure("Chat Analytics")
        
        
        ax_word_count_sender_1 = fig.add_axes((0.3, 0.08, 0.15, 0.8))
        ax_word_count_sender_2 = fig.add_axes((0.08, 0.08, 0.15, 0.8))
        ax_counter = fig.add_axes((0.52, 0.17, 0.45, 0.45))
        
        df = qmarks_counter.pivot(index='date', columns='sender', values='total')
        df = df.fillna(0)

        spearman_corr = round(df.iloc[:,[0, 1]].corr('spearman').iloc[:, 0][1], 2)
        df.iloc[:,0].plot(grid=True, label=df.iloc[:,0].name, legend=True, ax=ax_counter, figsize=(15, 7))
        df.iloc[:,1].plot(grid=True, label=df.iloc[:,1].name, legend=True, ax=ax_counter, figsize=(15, 7))
        
        sender_1_wordcount_df.sort_values(by='count').plot.barh(x='word', 
                                                                y='count', 
                                                                ax=ax_word_count_sender_1,
                                                                legend=False,
                                                                color='#ff7f0e',
                                                                xlabel='',
                                                                title=sender_1)
        
        sender_2_wordcount_df.sort_values(by='count').plot.barh(x='word',
                                                                y='count',
                                                                ax=ax_word_count_sender_2,
                                                                color='#1f77b4',
                                                                legend=False,
                                                                xlabel='',
                                                                title=sender_2)

        plt.title('? counter')
        plt.ylabel('? count')
        fig.text(.85, .63, f"spearman corr: {spearman_corr}", ha='left')
        plt.show()

@click.command()
@click.option('--filepath', '-f')
def main(filepath):
    chat = ChatAnalytics(chat_path=filepath)
    chat.run()

if __name__ == '__main__':
    main()