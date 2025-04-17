import pandas as pd

org_acc_df = pd.read_csv('./results-imagenet.csv')
prof_df = pd.read_csv('./benchmark-infer-amp-nchw-pt113-cu117-rtx3090.csv')

acc_df = org_acc_df.copy()
acc_df['pretrained'] = acc_df['model'].str.split('.').str[1]
acc_df['model'] = acc_df['model'].str.split('.').str[0]

# merge
merged_df = pd.merge(acc_df, prof_df, on='model', how='inner')
# efficiency metric
merged_df['efficiency'] = merged_df['top1'] / merged_df['infer_gmacs']
# sort by [efficiency]
merged_df = merged_df.sort_values(by=['efficiency'], ascending=False)
# reset index
merged_df = merged_df.reset_index(drop=True)
# print
print(merged_df.head(20))

print(merged_df.loc[merged_df['model'] == 'vit_base_patch32_224', ['model', 'pretrained', 'top1', 'infer_gmacs']], end='\n\n') # 4.41
print(merged_df.loc[merged_df['model'] == 'vit_base_patch16_224', ['model', 'pretrained', 'top1', 'infer_gmacs']], end='\n\n') # 17.58
print(merged_df.loc[merged_df['model'] == 'vit_huge_patch14_clip_224', ['model', 'pretrained', 'top1', 'infer_gmacs']], end='\n\n') # 167.4
print(merged_df.loc[(merged_df['infer_gmacs'] < 4.41) & (merged_df['infer_gmacs'] > 1), ['model', 'pretrained', 'top1', 'infer_gmacs']].sort_values(by=['top1'], ascending=False).head(5), end='\n\n')
print(merged_df.loc[(merged_df['infer_gmacs'] < 17.58) & (merged_df['infer_gmacs'] > 4.41), ['model', 'pretrained', 'top1', 'infer_gmacs']].sort_values(by=['top1'], ascending=False).head(5), end='\n\n')
print(merged_df.loc[(merged_df['infer_gmacs'] < 167.4) & (merged_df['infer_gmacs'] > 17.58), ['model', 'pretrained', 'top1', 'infer_gmacs']].sort_values(by=['top1'], ascending=False).head(5), end='\n\n')

print(merged_df.loc[(merged_df['model'].str.startswith("deit")), ['model', 'pretrained', 'top1', 'infer_gmacs']].sort_values(by=['top1'], ascending=False).head(5), end='\n\n')