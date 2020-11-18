import pandas as pd
import matplotlib.pyplot as plt
import click
from text_mining import TextCleaner

class ChatAnalytics:

    __is_ios = False

    def __init__(self, chat_path):
        with open(chat_path, 'r', encoding='utf-8') as h:
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


                coord = i.find(':')
                close_bracket = i.find(']')
                open_bracket = i.find('[')
                chat = i[close_bracket+1:]

                if coord > 0 and 'image omitted' not in chat:

                    sender = chat.split(":")[0].strip()
                    time_chat = i[open_bracket + 1:close_bracket]
                    date = time_chat.split()[0]

                    text = " ".join(chat.split(":")[1:]).strip()
                    if len(time_chat.split()) < 5 and len(date) >= 8:
                        chat_item = dict(
                            date=date,
                            time=time_chat.split()[1] if len(time_chat.split()) < 3 else f"{time_chat.split()[1]} {time_chat.split()[2]}",
                            sender=sender,
                            text=text
                        )

                        chat_dict.append(chat_item)
                    
            else:


                coord = i.find(':')
                if coord > 0 and 'image omitted' not in i:

                    chat = i[i.find("-")+1:]
                    time_chat = i.split("-")[0].replace(",", "")
                    date = time_chat.split()[0]
                    sender = chat[:chat.find(":")].strip()
                    text = chat[chat.find(":")+1:].strip()
                    if len(time_chat.split()) < 5 and len(date) >= 8:
                        chat_item = dict(
                            date=date,
                            time=time_chat.split()[1] if len(
                                time_chat.split()) < 3 else f"{time_chat.split()[1]} {time_chat.split()[2]}",
                            sender=sender,
                            text=text
                        )

                        chat_dict.append(chat_item)

        chat_df = pd.DataFrame(chat_dict)

        return chat_df

    def run(self):
        chat_df = self.__to_pandas()
        chat_df = chat_df[~chat_df.text.str.contains('end-to-end')]
        chat_df = chat_df[~chat_df.text.str.contains('omitted')]
        chat_df = chat_df[~chat_df.text.str.contains('voice')]
        senders = list(chat_df.sender.unique())
        sender_1 = senders[0]
        sender_2 = senders[1]
        
        sender_1_df = chat_df[chat_df.sender == sender_1]
        sender_2_df = chat_df[chat_df.sender == sender_2]
        
        sender_1_text = " ".join(list(sender_1_df.text))
        sender_2_text = " ".join(list(sender_2_df.text))

        if self.__is_ios:
            chat_df['CHAT_HOUR'] = chat_df['time'].apply(lambda x: f'{int(str(x).split(".")[0]):02d}' if len(x.split()) == 1 else f'{int(str(x).split(".")[0]):02d} {x.split()[1]}')
        else:
            chat_df['CHAT_HOUR'] = chat_df['time'].apply(lambda x: f'{int(str(x).split(".")[0]):02d}' if len(x.split()) == 1 else f'{int(str(x).split(":")[0]):02d} {x.split()[1]}')



        # wordcloud cleaner
        cleaner = TextCleaner()
        
        sender_1_wordcount_df = cleaner.get_clean_text(text=sender_1_text)
        sender_1_wordcount_df = sender_1_wordcount_df[sender_1_wordcount_df['count'] > 2]
        sender_1_wordcount_df = sender_1_wordcount_df.head(15)
        
        
        sender_2_wordcount_df = cleaner.get_clean_text(text=sender_2_text)
        sender_2_wordcount_df = sender_2_wordcount_df[sender_2_wordcount_df['count'] > 2]
        sender_2_wordcount_df = sender_2_wordcount_df.head(15)


        try:
            if self.__is_ios:
                chat_df.date = pd.to_datetime(chat_df.date, format="%d/%m/%y", errors='coerce')
                chat_df.date = chat_df.date.dt.tz_localize('UTC').dt.tz_convert('Asia/Jakarta')
            else:
                chat_df.date = pd.to_datetime(chat_df.date, format="%m/%d/%y", errors='coerce')
                chat_df.date = chat_df.date.dt.tz_localize('UTC').dt.tz_convert('Asia/Jakarta')
        except Exception as e:
            print(f"faield to covert to datetime format: {e}")

        # add total words
        chat_df['total_words'] = chat_df.text.apply(lambda x: len(str(x).split()))
        total_words_by_hour = chat_df.groupby(['sender', 'CHAT_HOUR']).total_words.\
              sum().\
              reset_index()

        total_words_by_hour = total_words_by_hour[total_words_by_hour.sender.isin([sender_1, sender_2])]
        total_words_by_hour_sender_1 = total_words_by_hour[total_words_by_hour.sender == sender_1]
        total_words_by_hour_sender_2 = total_words_by_hour[total_words_by_hour.sender == sender_2]

        total_words_by_hour_sender_1 = total_words_by_hour_sender_1.set_index('CHAT_HOUR').sort_index()
        total_words_by_hour_sender_2 = total_words_by_hour_sender_2.set_index('CHAT_HOUR').sort_index()



        total_words = chat_df.groupby(['date', 'sender'])['total_words'].sum() \
            .reset_index() \
            .rename(columns={'total_words': 'total'})
        
        total_words = total_words.sort_values(by='date')

        chat_df['?'] = chat_df['text'].str.contains("""[?]""").astype(int)
        qmarks_counter = chat_df.groupby(['date', 'sender'])['?'].sum()\
            .reset_index()\
            .rename(columns={'?': 'total'})
        qmarks_counter = qmarks_counter.sort_values(by='date')


        # visualize
        
        
        # plot size
        # plt.rcParams["figure.figsize"] = (15, 5)

        fig = plt.figure("Chat Analytics")
        
        # axes

        # ax word count
        ax_word_count_sender_1 = fig.add_axes((0.3, 0.08, 0.15, 0.4))
        ax_word_count_sender_2 = fig.add_axes((0.08, 0.08, 0.15, 0.4))

        # ax qmarks
        ax_qmarks = fig.add_axes((0.52, 0.15, 0.45, 0.3))
        ax_qmarks.set_title('? Counter')
        ax_qmarks.set_ylabel('total ?')

        # ax prime time
        ax_prime_time = fig.add_axes((0.07, 0.63, 0.38, 0.25))
        ax_prime_time.set_title('Prime Time')
        ax_prime_time.set_ylabel('total words')

        # ax total words
        ax_total_words = fig.add_axes((0.52, 0.58, 0.45, 0.3))
        ax_total_words.tick_params(
                        axis='x',          # changes apply to the x-axis
                        which='both',      # both major and minor ticks are affected
                        bottom=False,      # ticks along the bottom edge are off
                        top=False,         # ticks along the top edge are off
                        labelbottom=False)
        ax_total_words.set_title('Words')
        ax_total_words.set_ylabel('total words')
        ax_total_words.set_xlabel('date')
        

        qmarks_pivot = qmarks_counter.pivot(index='date', columns='sender', values='total')
        qmarks_pivot = qmarks_pivot.fillna(0)


        spearman_corr_qmarks = round(qmarks_pivot.iloc[:,[0, 1]].corr('spearman').iloc[:, 0][1], 2)

        qmarks_pivot.iloc[:,0].plot(grid=True, label=qmarks_pivot.iloc[:,0].name, legend=True, ax=ax_qmarks, figsize=(15, 7))
        qmarks_pivot.iloc[:,1].plot(grid=True, label=qmarks_pivot.iloc[:,1].name, legend=True, ax=ax_qmarks, figsize=(15, 7))
        
        # total words plot
        total_words_pivot = total_words.pivot(index='date', columns='sender', values='total')
        total_words_pivot = total_words_pivot.fillna(0)
        total_words_pivot.iloc[:, 0].plot(grid=True, 
                                          label=total_words_pivot.iloc[:, 0].name, legend=True,
                                          figsize=(15, 7),
                                          ax=ax_total_words,
                                          x=None)
        total_words_pivot.iloc[:, 1].plot(grid=True, 
                                          label=total_words_pivot.iloc[:, 1].name, legend=True,
                                          figsize=(15, 7),
                                          ax=ax_total_words,
                                          x=None)

        # prime time plot
        total_words_by_hour_sender_1['total_words'].plot(kind='bar',
                                                         position=1,
                                                         color='#ff7f0e',
                                                         label=sender_1,
                                                         figsize=(15, 7),
                                                         legend=False,
                                                         ax=ax_prime_time,
                                                         width=.35,
                                                         grid=True)
        total_words_by_hour_sender_2['total_words'].plot(kind='bar',
                                                         position=0,
                                                         color='#1f77b4',
                                                         label=sender_2,
                                                         figsize=(15, 7),
                                                         legend=False,
                                                         ax=ax_prime_time,
                                                         width=.35,
                                                         grid=True)

        
        # word count
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

        fig.text(.85, .46, f"spearman corr: {spearman_corr_qmarks}", ha='left')
        plt.show()

@click.command()
@click.option('--filepath', '-f')
def main(filepath):
    chat = ChatAnalytics(chat_path=filepath)
    chat.run()

if __name__ == '__main__':
    main()